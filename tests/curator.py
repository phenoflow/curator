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
