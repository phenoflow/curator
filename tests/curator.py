from curator.curator import Curator
from curator.curator_types import CuratorRepo


class TestCurator(Curator):

    __test__ = False

    def additionalPhenotypesFromHDR(
        self,
        phenotypeGroup: tuple[CuratorRepo, list[CuratorRepo]],
        repos: list[CuratorRepo],
    ) -> list[CuratorRepo]:
        return super()._additionalPhenotypesFromHDR(phenotypeGroup, repos)

    def removeUnrelatedPhenotypesUsingLLM(
        self, leadPhenotype: CuratorRepo, phenotypes: list[CuratorRepo]
    ) -> list[CuratorRepo]:
        return super()._removeUnrelatedPhenotypesUsingLLM(leadPhenotype, phenotypes)

    def removeDuplicates(
        self,
        possibleDuplicates: list[CuratorRepo],
        phenotypeGroups: dict[CuratorRepo, list[CuratorRepo]],
        ignore: list[CuratorRepo],
    ) -> dict[CuratorRepo, list[CuratorRepo]]:
        return super()._removeDuplicates(possibleDuplicates, phenotypeGroups, ignore)
