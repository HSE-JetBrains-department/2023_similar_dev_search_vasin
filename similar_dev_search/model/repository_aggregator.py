import asyncio
from collections import Counter, defaultdict
from typing import List, Tuple

import httpx
from tqdm import tqdm

from model.constants import N_REPOS_FROM_STARGAZERS
from model.developer import Developer
from model.developer_entry import DeveloperEntry
from model.repository import Repository


class RepositoryAggregator:
    def __init__(self, starting_repo: Repository):
        self.starting_repo = starting_repo
        self.top_repos = Counter()
        self.developers_dict = None
        self.developers_list = None
        self.repos = None

    async def get_developers(self, asyncio_client: httpx.AsyncClient = None) -> List[Developer]:
        """
        Returns a dict for each developer with their languages and variables
        :param asyncio_client:
        :return: dict of tuple of dicts - for languages and variables respectively
        """
        if self.developers_list is not None:
            return self.developers_list

        if asyncio_client is None:
            client = httpx.AsyncClient(timeout=None)
        else:
            client = asyncio_client

        self.developers_dict = defaultdict(DeveloperEntry)
        tasks = []
        for repo in tqdm((await self.get_repos(client))[:N_REPOS_FROM_STARGAZERS], "Analyzing repos"):
            tasks.append(repo.get_developers())

        result = await asyncio.gather(*tasks)

        for gathered_devs in tqdm(result, "Processing developers: " + str(len(result))):
            for developer, (languages, variables) in gathered_devs:
                for language, count in languages:
                    self.developers_dict[developer][0][language] += count
                for variable, count in variables:
                    self.developers_dict[developer][0][variable] += count

        self.developers_list = []
        for developer, (languages, variables) in self.developers_dict:
            gathered_dev = Developer(developer)
            gathered_dev.languages = languages
            gathered_dev.variables = variables
            self.developers_list.append(gathered_dev)

        await client.aclose()

        return self.developers_list

    async def get_repos(self, asyncio_client: httpx.AsyncClient = None) -> List[Repository]:
        """
        Return list of most popular repositories for stargazers of initial repo
        :param asyncio_client:
        :return:
        """
        if self.repos is not None:
            return self.repos

        if asyncio_client is None:
            client = httpx.AsyncClient(timeout=None)
        else:
            client = asyncio_client

        stargazers = [Developer(url) for url in await self.starting_repo.get_stargazers()]
        self.top_repos = Counter()
        tasks = []

        for stargazer in stargazers:
            tasks.append(stargazer.get_stargazed_repos(client))

        result = await asyncio.gather(*tasks)

        for repos in result:
            for repo in repos:
                self.top_repos[repo.url] += 1

        sorted_repos = [Repository(url) for url, _ in self.top_repos.most_common()]

        self.repos = sorted_repos
        await client.aclose()

        return self.repos
