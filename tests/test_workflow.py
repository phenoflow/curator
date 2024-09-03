import sys
import pytest  # type: ignore
from dotenv import load_dotenv

from curator.workflow import Workflow
from util.set_tuple_encoder import SetTupleEncoder
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


def test_getPhenotypeGroups() -> None:
    phenotypeGroups: dict[CuratorRepo, list[CuratorRepo]] = getPhenotypeGroups()
    assert len(phenotypeGroups) == 135


def test_workflowIntersection() -> None:
    repoToSteps: dict[CuratorRepo, list[str]] = CuratorGithub().getRepoToSteps()
    intersections: dict[
        CuratorRepo, dict[tuple[CuratorRepo, CuratorRepo], set[tuple[str, str]]]
    ] = Workflow().getIntersections(
        {key: repoToSteps[key] for key in list(repoToSteps)[: sys.maxsize]},
        getPhenotypeGroups(),
    )
    assert len(intersections) == 135
