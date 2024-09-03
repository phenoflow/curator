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
    assert TestWorkflow().workflowStepAnalysis(
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
    assert TestWorkflow().workflowStepAnalysis(
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
