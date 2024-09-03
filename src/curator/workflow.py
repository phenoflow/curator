from functools import reduce
import logging, re, os, pickle
import spacy  # type: ignore
from fuzzywuzzy import fuzz  # type: ignore

from curator.curator_types import CuratorRepo


class Workflow:

    def __init__(self) -> None:
        self.__logger: logging.Logger = logging.getLogger()
        self.__ignoreInStepNameCache: dict[str, bool] = {}
        self.__cache: dict[tuple[str, str], float] = {}
        self.__nlp = spacy.load('en_core_web_sm')

    def __ignoreInStepName(self, word: str) -> bool:
        if len(word) == 0:
            self.__logger.warning('zero length word passed')
            return True
        if word.isdigit():
            return False
        if word in self.__ignoreInStepNameCache:
            return self.__ignoreInStepNameCache[word]
        phenotypeSynonyms: list[str] = [
            'syndrome',
            'infection',
            'infections',
            'disease',
            'diseases',
            'disorder',
            'disorders',
            'malignancy',
            'status',
            'diagnosis',
            'dysfunction',
            'accident',
            'difficulty',
            'symptom',
            'symptoms',
        ]
        ignoreWords: list[str] = ['not', 'use', 'type', 'using', 'anything', 'enjoying']
        tag: str = self.__nlp(word)[0].pos_
        ignore: bool = (
            len(word) <= 2
            or word.lower() in phenotypeSynonyms + ignoreWords
            or (tag == 'CCONJ' or tag == 'SCONJ')
            or tag == 'ADP'
            or tag == 'ADV'
        )
        self.__ignoreInStepNameCache[word] = ignore
        return ignore

    def _isNegative(self, phrase: str) -> bool:
        phrase = phrase.lower()
        words: list[str] = phrase.split(' ')
        return (
            'not' in words
            or 'never' in words
            or 'no' in words
            or 'without' in words
            or any([word.startswith('non') for word in words])
            or any([word.startswith('un') for word in words])
        )

    def __compareTwoStrings(self, str1: str, str2: str) -> float:
        if (str1, str2) in self.__cache:
            return self.__cache[(str1, str2)]
        similarity: float = fuzz.ratio(str1, str2) / 100.0
        self.__cache[(str1, str2)] = similarity
        return similarity

    def __workflowStepAnalysis(
        self,
        workflowA: CuratorRepo,
        workflowStepA: str,
        workflowB: CuratorRepo,
        workflowStepB: str,
    ) -> bool:
        SIMILARITY_THRESHOLD: float = 0.8
        for workflowStepANameComponent in workflowStepA.split('---')[0].split('-'):
            if self.__ignoreInStepName(workflowStepANameComponent):
                continue
            for workflowStepBNameComponent in workflowStepB.split('---')[0].split('-'):
                if self.__ignoreInStepName(workflowStepBNameComponent):
                    continue
                if (
                    (workflowStepANameComponent.lower() in workflowA.name.lower())
                    and workflowStepBNameComponent.lower() in workflowB.name.lower()
                ) or (
                    (workflowA.name.lower() in workflowStepANameComponent.lower())
                    and workflowB.name.lower() in workflowStepBNameComponent.lower()
                ):
                    return False
                return (
                    self.__compareTwoStrings(
                        workflowStepANameComponent, workflowStepBNameComponent
                    )
                    > SIMILARITY_THRESHOLD
                )
        return False

    def __samePhenotype(self, nameA: str, nameB: str, similarity: bool = False) -> bool:

        SIMILARITY_THRESHOLD: float = 0.9

        def clean(input: str) -> str:
            return re.sub(r'[^a-zA-Z0-9]', '', input.lower())

        nameA = ' '.join(
            list(
                filter(
                    lambda word: not self.__ignoreInStepName(word),
                    nameA.split('---')[0].split('-'),
                )
            )
        )
        nameB = ' '.join(
            list(
                filter(
                    lambda word: not self.__ignoreInStepName(word),
                    nameB.split('---')[0].split('-'),
                )
            )
        )
        nameA = clean(nameA)
        nameB = clean(nameB)
        return (
            len(nameA) > 0
            and len(nameB) > 0
            and (
                (
                    self.__compareTwoStrings(nameA, nameB) > SIMILARITY_THRESHOLD
                    if similarity
                    else False
                )
                or nameA.startswith(nameB)
                or nameB.startswith(nameA)
            )
        )

    def getPhenotypeGroups(
        self, workflows: dict[CuratorRepo, list[str]]
    ) -> dict[CuratorRepo, list[CuratorRepo]]:
        phenotypeGroups: dict[CuratorRepo, list[CuratorRepo]] = {}
        path: str = 'output/phenotypeGroups.p'
        if os.path.exists(path):
            with open(path, 'rb') as file:
                phenotypeGroups = pickle.load(file)
                self.__logger.debug(phenotypeGroups)
                self.__logger.info(
                    'returning ' + str(len(phenotypeGroups)) + ' phenotype groups'
                )
                return phenotypeGroups
        iteration = 1
        for workflowA in list(workflows.keys()):
            if workflowA in [
                phenotype
                for sublist in list(phenotypeGroups.values())
                for phenotype in sublist
            ]:
                continue
            for workflowB in list(workflows.keys()):
                self.__logger.info(
                    str(
                        round(
                            (
                                iteration
                                / (
                                    len(list(workflows.keys()))
                                    * len(list(workflows.keys()))
                                )
                            )
                            * 100,
                            2,
                        )
                    )
                    + '%',
                )
                iteration += 1
                if workflowA == workflowB or workflowB in [
                    phenotype
                    for sublist in list(phenotypeGroups.items())
                    for phenotype in sublist
                ]:
                    continue
                if self.__samePhenotype(workflowA.name, workflowB.name):
                    phenotypeGroups.setdefault(workflowA, []).append(workflowB)
                    with open(path, 'wb') as f:
                        pickle.dump(phenotypeGroups, f)
        self.__logger.debug(phenotypeGroups)
        self.__logger.info(
            'returning ' + str(len(phenotypeGroups)) + ' phenotype groups'
        )
        return phenotypeGroups

    def getIntersections(
        self,
        workflows: dict[CuratorRepo, list[str]],
        phenotypeGroups: dict[CuratorRepo, list[CuratorRepo]],
    ) -> dict[CuratorRepo, dict[tuple[CuratorRepo, CuratorRepo], set[tuple[str, str]]]]:
        intersections: dict[
            CuratorRepo, dict[tuple[CuratorRepo, CuratorRepo], set[tuple[str, str]]]
        ] = {}
        path: str = 'output/intersections.p'
        if os.path.exists(path):
            with open(path, 'rb') as file:
                intersections = pickle.load(file)
                self.__logger.debug(intersections)
                self.__logger.info(
                    'returning '
                    + str(
                        reduce(
                            lambda acc, curr: acc + len(curr),
                            list(intersections.values()),
                            0,
                        )
                    )
                    + ' repos with common steps'
                )
                return intersections
        for phenotype, siblings in phenotypeGroups.items():
            intersection: dict[
                tuple[CuratorRepo, CuratorRepo], set[tuple[str, str]]
            ] = {}
            iteration: int = 1
            for workflowA in [phenotype] + siblings:
                for workflowB in [phenotype] + siblings:
                    if workflowA == workflowB or (workflowB, workflowA) in intersection:
                        continue
                    self.__logger.info(
                        str(
                            round(
                                (
                                    iteration
                                    / (
                                        len([phenotype] + siblings)
                                        * len([phenotype] + siblings)
                                    )
                                )
                                * 100,
                                2,
                            )
                        )
                        + '% ('
                        + str(list(phenotypeGroups.keys()).index(phenotype))
                        + ' of '
                        + str(len(phenotypeGroups))
                        + ')',
                    )
                    iteration += 1
                    for workflowStepA in list(
                        filter(
                            lambda sibling: sibling.endswith('.cwl'),
                            workflows[workflowA],
                        )
                    ):
                        if 'load' in workflowStepA or 'output' in workflowStepA:
                            continue
                        for workflowStepB in list(
                            filter(
                                lambda sibling: sibling.endswith('.cwl'),
                                workflows[workflowB],
                            )
                        ):
                            if (
                                ('load' in workflowStepB or 'output' in workflowStepB)
                                or (workflowStepA == workflowStepB)
                                or (
                                    (workflowA, workflowB) in intersection
                                    and (
                                        workflowStepB,
                                        workflowStepA,
                                    )
                                    in intersection[(workflowA, workflowB)]
                                )
                                or (
                                    not self._isNegative(
                                        ' '.join(
                                            workflowStepA.split('---')[0].split('-')
                                        )
                                    )
                                    == self._isNegative(
                                        ' '.join(
                                            workflowStepB.split('---')[0].split('-')
                                        )
                                    )
                                )
                            ):
                                continue
                            # if not workflowStepA.split('---')[1] == workflowStepB.split('---')[1]: continue
                            if self.__workflowStepAnalysis(
                                workflowA, workflowStepA, workflowB, workflowStepB
                            ):
                                intersection.setdefault(
                                    (workflowA, workflowB), set()
                                ).add((workflowStepA, workflowStepB))
            intersections[phenotype] = intersection
            with open(path, 'wb') as f:
                pickle.dump(intersections, f)
        self.__logger.debug(intersections)
        self.__logger.info(
            'returning '
            + str(
                reduce(
                    lambda acc, curr: acc + len(curr), list(intersections.values()), 0
                )
            )
            + ' repos with common steps'
        )
        return intersections
