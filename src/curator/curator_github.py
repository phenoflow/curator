import datetime, logging, os, pickle, time
from dotenv import load_dotenv
from github import Github
from github.Organization import Organization
from github.PaginatedList import PaginatedList
from github.Repository import Repository
from github.RateLimit import RateLimit
from github.ContentFile import ContentFile

from curator.curator_types import CuratorRepo


class CuratorGithub:

    def __init__(self) -> None:
        self.__logger: logging.Logger = logging.getLogger()
        self.__github: Github = Github(self.githubToken(), per_page=100)
        self.__phenoflow: Organization = self.__github.get_organization('phenoflow')

    def githubToken(self) -> str:
        load_dotenv()
        token: str | None = os.getenv('GITHUB_ACCESS_TOKEN')
        if not token:
            raise ValueError('GITHUB_ACCESS_TOKEN not found in .env file')
        return str(token)

    def __rateCheck(self) -> float:
        limit: RateLimit = self.__github.get_rate_limit()
        if limit.core.remaining < 10:
            return (
                limit.core.reset - datetime.datetime.now(datetime.UTC)
            ).total_seconds()
        return 0.0

    def repos(self) -> list[Repository]:
        repos: list[Repository] = []
        path: str = 'output/repos.p'
        if os.path.exists(path):
            with open(path, 'rb') as file:
                repos = pickle.load(file)
                self.__logger.debug(repos)
                self.__logger.info('returning ' + str(len(repos)) + ' repos')
                return repos

        paginatedRepos: PaginatedList[Repository] = self.__phenoflow.get_repos()
        pageNumber: int = 0
        while True:
            time.sleep(self.__rateCheck())
            page: list[Repository] = paginatedRepos.get_page(pageNumber)
            repos.extend(page)
            if len(page) < 100:
                break
            pageNumber += 1
        with open(path, 'wb') as f:
            pickle.dump(repos, f)
        self.__logger.debug(repos)
        self.__logger.info('returning ' + str(len(repos)) + ' repos')
        return repos

    def getRepoToSteps(self) -> dict[CuratorRepo, list[str]]:
        repoToSteps: dict[CuratorRepo, list[str]] = {}
        path: str = 'output/repoToSteps.p'
        if os.path.exists(path):
            with open(path, 'rb') as file:
                repoToSteps = pickle.load(file)
                self.__logger.debug(repoToSteps)
                self.__logger.info(str(len(repoToSteps)) + ' existing repo:step pairs')

        for repo in (repos := self.repos()):
            if len(repoToSteps) == len([repo for repo in repos if '---' in repo.name]):
                return repoToSteps
            self.__logger.info(
                str(round(repos.index(repo) / len(repos) * 100, 2)) + '%'
            )
            if '---' not in repo.name or repo.name in [
                storedRepo.name for storedRepo in list(repoToSteps.keys())
            ]:
                continue
            try:
                steps: list[str] = []
                contents: list[ContentFile] | ContentFile = repo.get_contents(
                    ''
                )  # ~MDC irritating return type...
                if type(contents) is list:
                    while contents:
                        time.sleep(self.__rateCheck())
                        content = contents.pop(0)
                        if content.type == 'dir':
                            newContents: list[ContentFile] | ContentFile = (
                                repo.get_contents(content.path)
                            )
                            if type(newContents) is list:
                                contents.extend(newContents)
                        else:
                            if '---' in content.name:
                                steps.append(content.name)
                    repoToSteps[
                        CuratorRepo(
                            repo.name, repo.description if repo.description else ''
                        )
                    ] = steps

                    with open(path, 'wb') as f:
                        pickle.dump(repoToSteps, f)
            except Exception as e:
                self.__logger.error(
                    f'error processing repository {repo.name}: {str(e)}'
                )
        self.__logger.debug(repoToSteps)
        self.__logger.info('returning ' + str(len(repoToSteps)) + ' repo:step pairs')
        return repoToSteps
