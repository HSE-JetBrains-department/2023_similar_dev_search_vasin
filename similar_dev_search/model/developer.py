from typing import List

import httpx

import model.fetcher as fetcher
from model.constants import headers
from model.repository import Repository


class Developer:
    def __init__(self, url: str):
        self.url = url
        url = url.replace('https://', '')
        url_prefix, id = url.split('/')
        self.id = id

    async def get_stargazes(self, asyncio_client: httpx.AsyncClient = None) -> List[Repository]:
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

    def __str__(self) -> str:
        return self.url


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
        response = await client.get(repos_url, headers=headers)
        repos_data = response.json()

        if asyncio_client is None:
            await client.aclose()

        repo_url_feature = "html_url"
        # print(repos_data)
        self.repos = [Repository(resp[repo_url_feature]) for resp in repos_data]
        return self.repos