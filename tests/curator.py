from curator.curator import Curator
from curator.curator_types import CuratorRepo


class TestCurator(Curator):

    __test__ = False

    def additionalConditionsFromHDR(
        self,
        phenotypeGroup: tuple[CuratorRepo, list[CuratorRepo]],
        repos: list[CuratorRepo],
    ) -> list[CuratorRepo]:
        return super()._additionalConditionsFromHDR(phenotypeGroup, repos)

    def removeUnrelatedConditionsUsingLLM(
        self, leadCondition: CuratorRepo, conditions: list[CuratorRepo]
    ) -> list[CuratorRepo]:
        return super()._removeUnrelatedConditionsUsingLLM(leadCondition, conditions)
