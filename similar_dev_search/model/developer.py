from collections import Counter
from typing import List

import httpx
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity

import model.fetcher as fetcher
from model.repository import Repository


class Developer:
    def __init__(self, url: str):
        self.languages = Counter()
        self.variables = Counter()
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

    def get_languages(self) -> Counter:
        """
        Gets dict of languages used by the developer
        :param asyncio_client: asyncio client to perform requests from
        :return: dict with language key and number of occurrences value
        """
        return self.languages

    def get_variables(self) -> Counter:
        """
        Gets dict of variables used by the developer
        :param asyncio_client:  asyncio client to perform requests from
        :return: dict with variable key and number of occurrences value
        """
        return self.variables

    def __str__(self) -> str:
        return f"{self.url}: most popular languages: {self.get_languages().most_common(3)}, " \
               f"variables: {self.get_variables().most_common(3)}"

    async def get_total_dict(self) -> dict[int]:
        """
        Gets united dict for languages and variables
        :return: dict of languages, variables and their respective occurrences
        """
        total_dict = dict()
        for variable in (self.get_variables()).keys():
            total_dict[variable] = (self.get_variables())[variable]

        for language in (self.get_languages()).keys():
            total_dict[language] = (self.get_languages())[language]

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
