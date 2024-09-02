import json, sys

import pytest  # type: ignore
from dotenv import load_dotenv

from curator.curator_types import CuratorRepo
from curator.curator_github import CuratorGithub
from curator.workflow import Workflow
from curator.curator import Curator
from util.set_tuple_encoder import SetTupleEncoder
from tests.curator import TestCurator


@pytest.fixture(scope='session', autouse=True)
def load_env() -> None:
    load_dotenv()


def test_removeUnrelatedConditionsUsingLLM() -> None:
    curator: TestCurator = TestCurator()
    assert curator.removeUnrelatedConditionsUsingLLM(
        CuratorRepo('Type 1 Diabetes', ''),
        [
            CuratorRepo('Type 2 Diabetes', ''),
            CuratorRepo('Metformin', ''),
            CuratorRepo('Insulin', ''),
        ],
    ) == [CuratorRepo('Insulin', '')]


def getPhenotypeGroups() -> dict[CuratorRepo, list[CuratorRepo]]:
    repoToSteps: dict[CuratorRepo, list[str]] = CuratorGithub().getRepoToSteps()
    return Curator().getPhenotypeGroups(
        {key: repoToSteps[key] for key in list(repoToSteps)[: sys.maxsize]}
    )


def test_getPhenotypeGroups_Curator() -> None:
    phenotypeGroups: dict[CuratorRepo, list[CuratorRepo]] = getPhenotypeGroups()
    assert len(phenotypeGroups) == 135
    with open('phenotypeGroups.json', 'w') as file:
        file.write(json.dumps(phenotypeGroups, cls=SetTupleEncoder, indent=2))


def test_workflowIntersection_Curator() -> None:
    repoToSteps: dict[CuratorRepo, list[str]] = CuratorGithub().getRepoToSteps()
    workflowIntersections: dict[
        CuratorRepo, dict[tuple[CuratorRepo, CuratorRepo], set[tuple[str, str]]]
    ] = Workflow().workflowIntersections(
        {key: repoToSteps[key] for key in list(repoToSteps)[: sys.maxsize]},
        getPhenotypeGroups(),
    )
    assert len(workflowIntersections) == 135
    with open('workflowIntersections.json', 'w') as file:
        file.write(json.dumps(workflowIntersections, cls=SetTupleEncoder, indent=2))
