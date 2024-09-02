import json
import pytest  # type: ignore
from dotenv import load_dotenv

from github.Repository import Repository

from util.set_tuple_encoder import SetTupleEncoder
from curator.curator_github import CuratorGithub
from curator.curator_types import CuratorRepo


@pytest.fixture(scope='session', autouse=True)
def load_env() -> None:
    load_dotenv()


def test_repos() -> None:
    repos: list[Repository] = CuratorGithub().repos()
    assert len(repos)
    with open('repos.json', 'w') as file:
        file.write(
            json.dumps([repo.name for repo in repos], cls=SetTupleEncoder, indent=2)
        )


def test_getRepoToSteps() -> None:
    repoToSteps: dict[CuratorRepo, list[str]] = CuratorGithub().getRepoToSteps()
    assert len(repoToSteps)
    with open('repoToSteps.json', 'w') as file:
        file.write(json.dumps(repoToSteps, cls=SetTupleEncoder, indent=2))
