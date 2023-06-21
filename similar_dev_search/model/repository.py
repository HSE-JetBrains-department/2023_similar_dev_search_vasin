import os
from collections import Counter, defaultdict
from typing import List, Tuple

import httpx
import pydriller
from pydriller import ModifiedFile
from tqdm import tqdm

import model.fetcher as fetcher
from git import Repo

from model.constants import COMMITS_PER_REPO
from model.language_extractor import fetch_language_variables


class Repository:
    def __init__(self, url):
        self.url = url
        self.languages = None
        self.variables = None
        self.stargazers = None
        self.developers = None
        self.dev_id = self.url.split('/')[-2]
        self.repo_name = self.url.split('/')[-1]
        self.repo_path = f'repositories/{self.repo_name}'

        if not os.path.exists(self.repo_path):
            Repo.clone_from(self.url, self.repo_path)

    def __str__(self):
        return self.url

    async def _add_file_info(self, author_id: str, file: ModifiedFile) -> None:
        """
        Add information about modified file to developer information.
        :param author_id: Unique name of GitHub developer.
        :param file: File from GitHub repository.
        :param repo_name: Name of repository.
        """
        if file.content:
            languages, variables = await fetch_language_variables(self.repo_path, file.filename,
                                                                  source_code=file.content)
            for variable, count in variables:
                self.developers[author_id][1][variable] += count
            for language, count in languages:
                self.developers[author_id][0][language] += count

    async def get_developers(self) -> Counter[Tuple[Counter, Counter]]:
        """
        Extract info about developers and their commits.
        :param path_to_repo: Path to GitHub repository.
        :return dict key = developer url, value = tuple of languages and variables dicts
        """
        if self.developers is not None:
            return self.developers

        self.developers = defaultdict[Tuple[Counter, Counter]]()

        try:
            for commit in tqdm(list((pydriller.Repository(self.repo_path)).traverse_commits())[:COMMITS_PER_REPO],
                               "Parsing commits for " + self.url):
                author_id = commit.author.email

                for file in commit.modified_files:
                    await self._add_file_info(author_id, file)
        except Exception as error:
            print('Something went wrong when analyzing ' + self.url + '.git: ' + str(error))
            pass
        return self.developers

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
