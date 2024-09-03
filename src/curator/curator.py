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
            return [
                list(filter(lambda repo: result['phenotype_id'] in repo.about, repos))[
                    0
                ]
                for result in results
                if result['phenotype_id'] not in existingIds
            ]
        else:
            return []

    def _removeUnrelatedPhenotypesUsingLLM(
        self, leadPhenotype: CuratorRepo, phenotypes: list[CuratorRepo]
    ) -> list[CuratorRepo]:

        message: str = (
            'Identify the numbers of the conditions below that are not synonyms for, or involved in the treatment of, '
            + self.__getPhenotype(leadPhenotype.name)
            + ':\n'
            + '\n'.join(
                [
                    str(phenotypes.index(condition))
                    + ': '
                    + self.__getPhenotype(condition.name)
                    for condition in phenotypes
                ]
            )
            + '\nPrint these numbers as a list (e.g. [1, 2, 3]). This list must be the last thing in your response.'
        )
        self.__logger.debug(message)
        response: str = self.__LLMClient.sendMessage(message)
        self.__logger.debug(response)
        try:
            extracted: str | None = (
                match.group(1)
                if (match := re.search(r'\[([0-9,\s]*)\]', response.strip()))
                else None
            )
            if extracted:
                return [
                    condition
                    for condition in phenotypes
                    if str(phenotypes.index(condition)) not in extracted.split(', ')
                ]
            else:
                raise Exception
        except:
            self.__logger.warning('unable to extract removals from: ' + response)
        return phenotypes

    def getPhenotypeGroups(
        self,
        reposToSteps: dict[CuratorRepo, list[str]],
    ) -> dict[CuratorRepo, list[CuratorRepo]]:
        phenotypeGroups: dict[CuratorRepo, list[CuratorRepo]] = (
            self.__workflow.getPhenotypeGroups(reposToSteps)
        )
        original = list(phenotypeGroups.keys())
        for phenotypeGroup in list(
            dict(
                sorted(
                    phenotypeGroups.items(),
                    key=lambda group: len(group[1]),
                    reverse=True,
                )
            ).items()
        )[: int(self.__config.get('CURATOR', 'MAX_LLM'))]:
            phenotypeGroups[phenotypeGroup[0]] = (
                self._removeUnrelatedPhenotypesUsingLLM(
                    phenotypeGroup[0],
                    phenotypeGroup[1]
                    + self._additionalPhenotypesFromHDR(
                        phenotypeGroup, list(reposToSteps.keys())
                    ),
                )
            )
        return {repo: phenotypeGroups[repo] for repo in original}

    def getIntersections(
        self, workflows: dict[CuratorRepo, list[str]]
    ) -> dict[CuratorRepo, dict[tuple[CuratorRepo, CuratorRepo], set[tuple[str, str]]]]:
        return self.__workflow.getIntersections(
            workflows, self.getPhenotypeGroups(workflows)
        )
