from curator.curator_types import CuratorRepo
from curator.workflow import Workflow


class TestWorkflow(Workflow):

    __test__ = False

    def isNegative(self, phrase: str) -> bool:
        return super()._isNegative(phrase)

    def workflowStepAnalysis(
        self,
        workflowA: CuratorRepo,
        workflowStepA: str,
        workflowB: CuratorRepo,
        workflowStepB: str,
    ) -> bool:
        return super()._workflowStepAnalysis(
            workflowA, workflowStepA, workflowB, workflowStepB
        )
