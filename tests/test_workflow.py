import sys
import pytest  # type: ignore
from dotenv import load_dotenv

from curator.workflow import Workflow
from tests.workflow import TestWorkflow
from curator.curator_github import CuratorGithub
from curator.curator_types import CuratorRepo


@pytest.fixture(scope='session', autouse=True)
def load_env() -> None:
    load_dotenv()


def test_workflowStepAnalysis() -> None:
    testWorkflow: TestWorkflow = TestWorkflow()
    assert testWorkflow.workflowStepAnalysis(
        CuratorRepo(
            'Diabetes---b8c00ec0-19ee-11ef-9de4-4d4ea830ad16', 'Diabetes - PH520'
        ),
        'exudative-diabetes---primary.cwl',
        CuratorRepo(
            'Diabetes-Mellitus---872f75f0-20c7-11ef-ba9f-3d1e4076db47',
            'Diabetes Mellitus - PH419',
        ),
        'exudative-diabetes-mellitus---primary.cwl',
    )
    assert testWorkflow.workflowStepAnalysis(
        CuratorRepo(
            'Diabetes---b8c00ec0-19ee-11ef-9de4-4d4ea830ad16', 'Diabetes - PH520'
        ),
        'diabetes-admission---primary.cwl',
        CuratorRepo(
            'Diabetes-Mellitus---872f75f0-20c7-11ef-ba9f-3d1e4076db47',
            'Diabetes Mellitus - PH419',
        ),
        'diabetes-mellitus-admission---primary.cwl',
    )
    assert not testWorkflow.workflowStepAnalysis(
        CuratorRepo(
            'Dementia---1e979480-1877-11ef-9de4-4d4ea830ad16', 'Dementia - PH417'
        ),
        'dementia-dementium---primary.cwl',
        CuratorRepo(
            'Dementia---175e62d0-1b50-11ef-9de4-4d4ea830ad16',
            'Dementia (P13) - PH6599',
        ),
        'cerebral-dementia-p13---primary.cwl',
    )
    assert not testWorkflow.workflowStepAnalysis(
        CuratorRepo(
            'COVID-19-infection---0ad8bf70-16ea-11ef-9de4-4d4ea830ad16',
            'COVID-19 infection - PH1',
        ),
        'acute-covid-19-infection---primary.cwl',
        CuratorRepo(
            'Long-covid---4bb839e0-397b-11ef-918f-350181f4a5db',
            'Long covid - ZhuuOh7JC1cUoRzdSzvH5pas6k',
        ),
        'clinic-long-covid---primary.cwl',
    )
    assert not testWorkflow.workflowStepAnalysis(
        CuratorRepo(
            'Cardiovascular-Disease---99107750-16f0-11ef-9de4-4d4ea830ad16',
            'Cardiovascular Disease (Psoriasis Association Study with CVD) - PH6',
        ),
        'cardiovascular-disease-psoriasis-association-study-with-cvd-asystole---primary.cwl',
        CuratorRepo(
            'Cardiovascular-Disease-Risk-Score---e69ab730-1a36-11ef-9de4-4d4ea830ad16',
            'Cardiovascular Disease (CVD) Risk Score - PH579',
        ),
        'cardiovascular-disease-cvd-risk-score---primary.cwl',
    )
    assert not testWorkflow.workflowStepAnalysis(
        CuratorRepo(
            'Diabetes---94b07310-1d47-11ef-94c0-09c4aef33dd',
            'Diabetes (Diagnostic Code) - PH895',
        ),
        'diabetes-diagnostic-code-ketoacidosis---primary.cwl',
        CuratorRepo(
            'Diabetes---74eb7c70-1d4a-11ef-94c0-09c4aef33dd3',
            'Diabetes (Drug Code) - PH896',
        ),
        'diabetes-drug-code-sitagliptin---primary.cwl',
    )
    assert not testWorkflow.workflowStepAnalysis(
        CuratorRepo(
            'Diabetes---87522990-184a-11ef-9de4-4d4ea830ad16',
            'Diabetes - PH375',
        ),
        'stable-diabetes---primary.cwl',
        CuratorRepo(
            'Thiazolidinediones---b8c49280-1c26-11ef-bdee-f10829e63eeb',
            'Thiazolidinediones - PH751',
        ),
        'thiazolidinediones-tablet---primary.cw',
    )


def getPhenotypeGroups() -> dict[CuratorRepo, list[CuratorRepo]]:
    repoToSteps: dict[CuratorRepo, list[str]] = CuratorGithub().getRepoToSteps()
    return Workflow().getPhenotypeGroups(
        {key: repoToSteps[key] for key in list(repoToSteps)[: sys.maxsize]}
    )


def test_isNegative() -> None:
    assert TestWorkflow().isNegative(
        ' '.join('anxiety-specified---primary.cwl'.split('---')[0].split('-'))
    ) != TestWorkflow().isNegative(
        ' '.join('anxiety-unspecified---icd.cwl'.split('---')[0].split('-'))
    )


def test_getPhenotypeGroups() -> None:
    phenotypeGroups: dict[CuratorRepo, list[CuratorRepo]] = getPhenotypeGroups()
    assert len(phenotypeGroups)


def test_workflowIntersection() -> None:
    repoToSteps: dict[CuratorRepo, list[str]] = CuratorGithub().getRepoToSteps()
    intersections: dict[
        CuratorRepo, dict[tuple[CuratorRepo, CuratorRepo], set[tuple[str, str]]]
    ] = Workflow().getIntersections(
        {key: repoToSteps[key] for key in list(repoToSteps)[: sys.maxsize]},
        getPhenotypeGroups(),
    )
    assert len(intersections)
