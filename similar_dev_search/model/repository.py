from typing import List
import httpx

import model.fetcher as fetcher


class Repository:
    def __init__(self, url):
        self.url = url
        self.languages = None
        self.variables = None
        self.stargazers = None
        self.developers = None
        self.dev_id = self.url.split('/')[-2]
        self.repo_name = self.url.split('/')[-1]

    def __str__(self):
        return self.url

    async def get_stargazers(self, asyncio_client: httpx.AsyncClient = None) -> List[str]:
        """
        Gets list of stargazers' urls
        :param asyncio_client:
        :return: list of urls of stargazers of the repo
        """
        if self.stargazers is not None:
            return self.stargazers

        if asyncio_client is None:
            client = httpx.AsyncClient(timeout=None)
        else:
            client = asyncio_client

        developers_urls = await fetcher.fetch_stargazers_for_repo(self.url)

        await client.aclose()
        return developers_urls

