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
