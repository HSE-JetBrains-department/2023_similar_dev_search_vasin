from collections import defaultdict
from typing import List

import httpx

import model.fetcher as fetcher
from model.repository import Repository


class Developer:
    def __init__(self, url: str):
        self.languages = defaultdict(int)
        self.variables = defaultdict(int)
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

    def get_languages(self) -> defaultdict[int]:
        """
        Gets dict of languages used by the developer
        :param asyncio_client: asyncio client to perform requests from
        :return: dict with language key and number of occurrences value
        """
        return self.languages

    def get_variables(self) -> defaultdict[int]:
        """
        Gets dict of variables used by the developer
        :param asyncio_client:  asyncio client to perform requests from
        :return: dict with variable key and number of occurrences value
        """
        return self.variables

    def __str__(self) -> str:
        return self.url
