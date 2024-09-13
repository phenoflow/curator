import json, sys, uuid

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


def test_removeDuplicates() -> None:
    assert TestCurator().removeDuplicates(
        [CuratorRepo('Metformin', '')],
        {
            CuratorRepo('Type 1 Diabetes', ''): [
                CuratorRepo('Metformin', ''),
            ],
            CuratorRepo('Type 2 Diabetes', ''): [
                CuratorRepo('Insulin', ''),
                CuratorRepo('Metformin', ''),
            ],
            CuratorRepo('COPD', ''): [
                CuratorRepo('Metformin', ''),
            ],
        },
        [CuratorRepo('Type 1 Diabetes', '')],
    ) == {
        CuratorRepo('Type 1 Diabetes', ''): [
            CuratorRepo('Metformin', ''),
        ],
        CuratorRepo('Type 2 Diabetes', ''): [
            CuratorRepo('Insulin', ''),
        ],
    }


def test_removeUnrelatedPhenotypesUsingLLM() -> None:
    assert TestCurator().removeUnrelatedPhenotypesUsingLLM(
        CuratorRepo('Type 1 Diabetes', ''),
        [
            CuratorRepo('Type 2 Diabetes', ''),
            CuratorRepo('Metformin', ''),
            CuratorRepo('Insulin', ''),
        ],
    ) == [CuratorRepo('Insulin', '')]


def getPhenotypeGroups() -> dict[CuratorRepo, list[CuratorRepo]]:
    repoToSteps: dict[CuratorRepo, list[str]] = CuratorGithub().getRepoToSteps()
    phenotypeGroups: dict[
        CuratorRepo, list[CuratorRepo]
    ] = Curator().getPhenotypeGroups(
        {key: repoToSteps[key] for key in list(repoToSteps)[: sys.maxsize]}
    )
    with open('phenotypeGroups.json', 'w') as file:
        file.write(json.dumps(phenotypeGroups, cls=SetTupleEncoder, indent=2))
    return phenotypeGroups


def test_getPhenotypeGroups_Curator() -> None:
    assert len(getPhenotypeGroups())


def test_workflowIntersection_Curator() -> None:
    repoToSteps: dict[CuratorRepo, list[str]] = CuratorGithub().getRepoToSteps()
    intersections: dict[
        CuratorRepo, dict[tuple[CuratorRepo, CuratorRepo], set[tuple[str, str]]]
    ] = Workflow().getIntersections(
        {key: repoToSteps[key] for key in list(repoToSteps)[: sys.maxsize]},
        getPhenotypeGroups(),
    )
    assert len(intersections)
    with open('intersections.json', 'w') as file:
        file.write(json.dumps(intersections, cls=SetTupleEncoder, indent=2))
