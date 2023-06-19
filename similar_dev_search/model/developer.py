from collections import defaultdict
from typing import List, Tuple

import httpx
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity

import model.fetcher as fetcher
from model.constants import HEADERS, REPOS_LIMIT
from model.repository import Repository


class Developer:
    def __init__(self, url: str):
        self.languages = None
        self.variables = None
        self.repos = None
        self.url = url
        url = url.replace('https://', '')
        url_prefix, id = url.split('/')
        self.id = id

    async def get_stargazed_repos(self, asyncio_client: httpx.AsyncClient = None) -> List[Repository]:
        """
        Gets list of stargazed repositories
        :param asyncio_client: asyncio client to perform requests from
        :return: stargazed repositories
        """
        page_url_template = "https://api.github.com/users/" + self.id + "/starred?page={}&per_page=100"

        if asyncio_client is None:
            client = httpx.AsyncClient(timeout=None)
        else:
            client = asyncio_client

        starred_repos = await fetcher.fetch_all_repos_for_developer(page_url_template, self.id, client)
        if asyncio_client is None:
            await client.aclose()

        return starred_repos

    async def get_languages(self, asyncio_client: httpx.AsyncClient = None) -> defaultdict[int]:
        """
        Gets dict of languages used by the developer
        :param asyncio_client: asyncio client to perform requests from
        :return: dict with language key and number of occurrences value
        """
        if self.languages is not None:
            return self.languages
        languages, _ = await self.get_languages_variables(asyncio_client)
        return languages

    async def get_variables(self, asyncio_client: httpx.AsyncClient = None) -> defaultdict[int]:
        """
        Gets dict of variables used by the developer
        :param asyncio_client:  asyncio client to perform requests from
        :return: dict with variable key and number of occurrences value
        """
        if self.variables is not None:
            return self.variables
        _, variables = await self.get_languages_variables(asyncio_client)
        return variables

    async def get_languages_variables(self, asyncio_client: httpx.AsyncClient = None) \
            -> Tuple[defaultdict[int], defaultdict[int]]:
        """
        Gets both languages and variables that developer uses
        :param asyncio_client:  asyncio client to perform requests from
        :return: dict of languages, dict of variables
        """
        if self.languages is not None and self.variables is not None:
            return self.languages, self.variables
        self.languages = defaultdict(int)
        self.variables = defaultdict(int)
        repos = await self.get_repos()

        for i in range(min(REPOS_LIMIT, len(repos))):
            for language in (await repos[i].get_languages(asyncio_client)).keys():
                self.languages[language] += (await repos[i].get_languages(asyncio_client))[language]
            for variable in (await repos[i].get_variables(asyncio_client)).keys():
                self.languages[variable] += (await repos[i].get_variables(asyncio_client))[variable]
        return self.languages, self.variables

    def __str__(self) -> str:
        return self.url

    async def get_total_dict(self) -> dict[int]:
        """
        Gets united dict for languages and variables
        :return: dict of languages, variables and their respective occurrences
        """
        total_dict = dict()
        for variable in (await self.get_variables()).keys():
            total_dict[variable] = (await self.get_variables())[variable]

        for language in (await self.get_languages()).keys():
            total_dict[language] = (await self.get_languages())[language]

        return total_dict

    async def compute_similarity(self, other: 'Developer') -> float:
        """
        Calculates similarity between self and other developer
        :param other: developer to compute similarity to
        :return: a float - cosine similarity of list of common variables and languages
        """
        my_total_dict = await self.get_total_dict()
        other_total_dict = await other.get_total_dict()

        for entry in my_total_dict:
            if entry not in other_total_dict:
                other_total_dict[entry] = 0

        for entry in other_total_dict:
            if entry not in my_total_dict:
                my_total_dict[entry] = 0

        my_df = pd.DataFrame(my_total_dict, index=[0])
        other_df = pd.DataFrame(other_total_dict, index=[0])
        if len(my_df.keys()) == 0:
            return 0.0
        return cosine_similarity(
            my_df, other_df
        ).reshape(-1)

    async def get_repos(self, asyncio_client: httpx.AsyncClient = None) -> List[Repository]:
        """
        Gets list of repositories for the current deveoper
        :param asyncio_client: asyncio client to perform requests from
        :return: list of repositories that developer uses
        """
        if self.repos is not None:
            return self.repos

        if asyncio_client is None:
            client = httpx.AsyncClient(timeout=None)
        else:
            client = asyncio_client

        repos_url = f"https://api.github.com/users/{self.id}/repos"
        response = await client.get(repos_url, headers=HEADERS)
        repos_data = response.json()

        if asyncio_client is None:
            await client.aclose()

        repo_url_feature = "html_url"
        # print(repos_data)
        self.repos = [Repository(resp[repo_url_feature]) for resp in repos_data]
        return self.repos