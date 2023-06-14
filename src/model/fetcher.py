import asyncio
import os
from collections import defaultdict

import httpx
import itertools

from typing import List

from model.constants import headers, stargazer_pages_num, repos_pages_num
from model.repository import Repository


async def fetch_stargazers_for_page(client: httpx.AsyncClient, url, page):
    response = await client.get(url.format(page), headers=headers)
    return response.json()


async def fetch_stargazers_for_repo(asyncio_client: httpx.AsyncClient, url: str) -> List[str]:
    stargazers = set()
    tasks = []

    org, name = url.split('/')[-2:]
    url = f"https://api.github.com/repos/{org}/{name}"
    url += "/stargazers?page={}&per_page=100"

    if asyncio_client is None:
        client = httpx.AsyncClient(timeout=None)
    else:
        client = asyncio_client
    for page in range(1, stargazer_pages_num):
        tasks.append(
            fetch_stargazers_for_page(client, url, page))

    response = await asyncio.gather(*tasks)

    if asyncio_client is None:
        await client.aclose()

    for user_json in response:
        stargazers.update(list(map(lambda user: 'https://github.com/' + user["login"], user_json)))

    return list(stargazers)


async def fetch_all_repos(url, stargazers):
    async with httpx.AsyncClient(timeout=None) as client:
        repo_url_feature = "html_url"
        starred_repos = defaultdict(int)
        for stargazer_ind, stargazer in enumerate(stargazers):
            response = await asyncio.gather(
                *map(fetch_repos, itertools.repeat(client), itertools.repeat(url), itertools.repeat(stargazer),
                     list(range(1, repos_pages_num)))
            )
            for repo in response[0]:
                starred_repos[repo[repo_url_feature]] += 1
        return starred_repos


async def fetch_all_repos_for_stargazer(page_url_template: str, asyncio_client, stargazer_id: str) -> List[Repository]:
    repo_url_feature = "html_url"
    starred_repos = list()
    response = await asyncio.gather(
        *map(fetch_repos, itertools.repeat(asyncio_client), itertools.repeat(page_url_template),
             itertools.repeat(stargazer_id),
             list(range(1, repos_pages_num)))
    )
    for repo_json in response[0]:
        starred_repos.append(Repository(repo_json[repo_url_feature]))

    return starred_repos


async def fetch_repos(client: httpx.AsyncClient, page_url_template: str, stargazer_id: str, page: int):
    response = await client.get(page_url_template.format(stargazer_id, page), headers=headers)
    return response.json()
