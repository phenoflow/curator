import logging, re, configparser
from typing import Any
from pyconceptlibraryclient import Client, DOMAINS  # type: ignore

from curator.workflow import Workflow
from curator.curator_types import CuratorRepo
from llm.llm_client import LLMClient


class Curator:

    def __init__(self) -> None:
        self.__logger = logging.getLogger()
        self.__config: configparser.ConfigParser = configparser.ConfigParser()
        self.__config.read('config/config.ini')
        self.__workflow: Workflow = Workflow()
        self.__client: Client = Client(public=True, url=DOMAINS.HDRUK)
        self.__LLMClient = LLMClient(False)

    def __getPhenotype(self, repoName: str) -> str:
        return repoName.split('---')[0].replace('-', ' ')

    def _additionalPhenotypesFromHDR(
        self,
        phenotypeGroup: tuple[CuratorRepo, list[CuratorRepo]],
        repos: list[CuratorRepo],
    ) -> list[CuratorRepo]:
        searchName: str = self.__getPhenotype(phenotypeGroup[0].name)
        self.__logger.debug('searching for: ' + searchName)
        results: list[Any] = self.__client.phenotypes.get(search=searchName)
        if len(results) > 0:
            existingIds: list[str] = [
                curatorRepo.about.split(' - ')[1]
                for curatorRepo in [phenotypeGroup[0]] + phenotypeGroup[1]
                if '- PH' in curatorRepo.about
            ]

            def idToPhenotype(id: str) -> CuratorRepo | None:
                repoAsList: list[CuratorRepo] = list(
                    filter(lambda repo: id in repo.about, repos)
                )
                if len(repoAsList) > 0:
                    return repoAsList[0]
                else:
                    self.__logger.warning('no match on phenoflow for HDR id: ' + id)
                    return None

            return [
                repo
                for result in results
                if (repo := idToPhenotype(result['phenotype_id'])) is not None
                and result['phenotype_id'] not in existingIds
            ]
        else:
            return []

    def _removeUnrelatedPhenotypesUsingLLM(
        self, leadPhenotype: CuratorRepo, phenotypes: list[CuratorRepo]
    ) -> list[CuratorRepo]:

        def getIncluded(prompt: str) -> list[str]:
            promptPhenotypes: list[str] = sorted(
                list(
                    set(
                        [
                            self.__getPhenotype(phenotype.name)
                            for phenotype in phenotypes
                        ]
                    )
                )
            )
            formattedPhenotypes: str = (
                '\n'.join(
                    [
                        str(promptPhenotypes.index(condition) + 1)
                        + ': '
                        + condition
                        + ','
                        for condition in promptPhenotypes
                    ],
                )[:-1]
                + '.\nPrint all the correct answers as a list (e.g. [1, 2, 3]). '
                + 'If none of the answers are correct, print an empty list ([]). '
                + 'This list must be the last thing in your response.'
            )
            message: str = (
                'Which of the following ' + prompt + ':\n' + formattedPhenotypes
            )
            self.__logger.debug(message)
            response: str = self.__LLMClient.sendMessage(message)
            self.__logger.debug(response)
            try:
                extracted: str | None = (
                    match.group(1)
                    if (match := re.search(r'\[([0-9,\s]*?)\]', response.strip()))
                    else None
                )
                if extracted:
                    return [
                        promptPhenotypes[int(index) - 1]
                        for index in extracted.split(', ')
                    ]
                elif extracted != None and len(str(extracted)) == 0:
                    return []
                else:
                    raise Exception
            except:
                self.__logger.warning('unable to extract removals from: ' + response)
                return []

        exactMatches: list[CuratorRepo] = [
            phenotype
            for phenotype in phenotypes
            if phenotype != leadPhenotype
            and self.__getPhenotype(phenotype.name).lower().strip()
            == self.__getPhenotype(leadPhenotype.name).lower().strip()
        ]
        phenotypes = list(set(phenotypes) - set(exactMatches))

        synonyms: list[str] = getIncluded(
            'are another way of writing ' + self.__getPhenotype(leadPhenotype.name)
        )

        medications: list[str] = getIncluded(
            'are medications for ' + self.__getPhenotype(leadPhenotype.name)
        )

        subconditions: list[str] = getIncluded(
            'are subconditions (e.g. particular types) of '
            + self.__getPhenotype(leadPhenotype.name)
        )

        return exactMatches + [
            phenotype
            for phenotype in phenotypes
            if self.__getPhenotype(phenotype.name) in synonyms + medications
            and self.__getPhenotype(phenotype.name) not in subconditions
        ]

    def _removeDuplicates(
        self,
        possibleDuplicates: list[CuratorRepo],
        phenotypeGroups: dict[CuratorRepo, list[CuratorRepo]],
        ignore: list[CuratorRepo],
    ) -> dict[CuratorRepo, list[CuratorRepo]]:
        for possibleDuplicate in possibleDuplicates:
            for key in list(set(phenotypeGroups.keys()) - set(ignore)):
                phenotypeGroups[key] = [
                    phenotype
                    for phenotype in phenotypeGroups[key]
                    if phenotype != possibleDuplicate
                ]
                if not phenotypeGroups[key]:
                    del phenotypeGroups[key]
        return phenotypeGroups

    def getPhenotypeGroups(
        self,
        reposToSteps: dict[CuratorRepo, list[str]],
    ) -> dict[CuratorRepo, list[CuratorRepo]]:
        phenotypeGroups: dict[CuratorRepo, list[CuratorRepo]] = (
            self.__workflow.getPhenotypeGroups(reposToSteps)
        )
        for phenotypeGroup in list(
            dict(
                sorted(
                    phenotypeGroups.items(),
                    key=lambda group: len(group[1]),
                    reverse=True,
                )
            ).items()
        )[: int(self.__config.get('CURATOR', 'MAX_LLM'))]:
            originalPhenotypesInGroup: list[CuratorRepo] = phenotypeGroups[
                phenotypeGroup[0]
            ]
            phenotypeGroups[phenotypeGroup[0]] = (
                self._removeUnrelatedPhenotypesUsingLLM(
                    phenotypeGroup[0],
                    phenotypeGroup[1]
                    + self._additionalPhenotypesFromHDR(
                        phenotypeGroup, list(reposToSteps.keys())
                    ),
                )
            )
            phenotypeGroups = self._removeDuplicates(
                list(
                    set(phenotypeGroups[phenotypeGroup[0]])
                    - set(originalPhenotypesInGroup)
                ),
                phenotypeGroups,
                [phenotypeGroup[0]],
            )

        return phenotypeGroups

    def getIntersections(
        self, workflows: dict[CuratorRepo, list[str]]
    ) -> dict[CuratorRepo, dict[tuple[CuratorRepo, CuratorRepo], set[tuple[str, str]]]]:
        return self.__workflow.getIntersections(
            workflows, self.getPhenotypeGroups(workflows)
        )
