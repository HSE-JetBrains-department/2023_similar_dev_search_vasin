import asyncio
from collections import defaultdict

import httpx


import model.fetcher as fetcher
from model.constants import headers
from model.language_extractor import fetch_language_variables


class Repository:
    def __init__(self, url):
        self.url = url
        self.languages = None
        self.variables = None
        self.dev_id = self.url.split('/')[-2]
        self.repo_name = self.url.split('/')[-1]

    def get_stargazers(self):
        """
        Returns list of stargazers
        :return:
        """
        return fetcher.fetch_stargazers_for_repo(self.url)

    def __str__(self):
        return self.url

    async def get_languages(self, asyncio_client: httpx.AsyncClient = None) -> defaultdict[int]:
        """
        Returns dict of languages for this repo
        :param asyncio_client: asyncio client to perform requests from
        :return: dict {language: occurrences}
        """
        if self.languages is not None:
            return self.languages
        languages, _ = await self.get_languages_variables(asyncio_client)
        return languages

    async def get_variables(self, asyncio_client: httpx.AsyncClient = None) -> defaultdict[int]:
        """
        Returns dict of variables for this repo
        :param asyncio_client: asyncio client to perform requests from
        :return: dict {variable: occurrences}
        """
        if self.variables is not None:
            return self.variables
        _, variables = await self.get_languages_variables(asyncio_client)
        return variables

    async def get_languages_variables(self, asyncio_client: httpx.AsyncClient = None):
        """
        Returns dict of languages and dict of variables
        :param asyncio_client: asyncio client to perform requests from
        :return: dict of languages, dict of variables
        """
        if self.languages is not None and self.variables is not None:
            return self.languages, self.variables

        self.languages = defaultdict(int)
        self.variables = defaultdict(int)

        if asyncio_client is None:
            client = httpx.AsyncClient(timeout=None)
        else:
            client = asyncio_client

        files_url = f"https://api.github.com/repos/{self.dev_id}/{self.repo_name}/contents"
        response = await client.get(files_url, headers=headers)
        files_data = response.json()

        tasks = []
        for file in files_data:
            if file is not dict:
                continue
            if "type" not in file:
                continue
            if file["type"] == "file":
                file_path = file["path"]
                file_url = f"https://raw.githubusercontent.com/{self.dev_id}/{self.repo_name}/master/{file_path}"

                tasks.append(fetch_language_variables(file_url, file_path[file_path.find('/') + 1:], client))

        result = await asyncio.gather(*tasks)

        if asyncio_client is None:
            await client.aclose()
        for language, variables in result:
            if language == 'Ignore List' or language == '':
                continue
            self.languages[language] += 1
            for var in variables.keys():
                self.variables[var] += variables[var]
        return self.languages, self.variables
