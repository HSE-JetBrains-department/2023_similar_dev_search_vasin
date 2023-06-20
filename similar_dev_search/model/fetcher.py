import asyncio
import itertools
from typing import List

import httpx

from model.constants import headers, stargazer_pages_num, repos_pages_num
from model.repository import Repository


async def fetch_stargazers_for_page(client: httpx.AsyncClient, url, page):
    """
    For a given page, returns list of stargazer urls
    :param client:  asyncio client to perform requests from
    :param url: url string with a missing page format
    :param page: page number
    :return: Json with stargazers
    """
    response = await client.get(url.format(page), headers=headers)
    return response.json()


async def fetch_stargazers_for_repo(url: str, asyncio_client: httpx.AsyncClient = None) -> List[str]:
    """
    For a given repository url, returns list of stargazer urls
    :param asyncio_client: asyncio client to perform requests from
    :param url: url of the repository
    :return: list of stargazer urls
    """
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


async def fetch_all_repos_for_developer(page_url_template: str, developer_id: str,
                                        asyncio_client: httpx.AsyncClient = None) -> List[Repository]:
    """
    For a given developer id, returns all repositories urls
    :param page_url_template: a string template with developer id missing
    :param asyncio_client: asyncio client to perform requests from
    :param developer_id: id of a developer
    :return: list of repositories
    """
    repo_url_feature = "html_url"
    starred_repos = list()
    response = await asyncio.gather(
        *map(fetch_repos, itertools.repeat(asyncio_client), itertools.repeat(page_url_template),
             itertools.repeat(developer_id),
             list(range(1, repos_pages_num)))
    )
    for repo_json in response[0]:
        starred_repos.append(Repository(repo_json[repo_url_feature]))

    return starred_repos


async def fetch_repos(client: httpx.AsyncClient, page_url_template: str, developer_id: str, page: int):
    """
    For a given developer id and page number, get json with all repositories
    :param client: asyncio client to perform requests from
    :param page_url_template: a template for a page with missing developer id and page number
    :param developer_id: id of developer
    :param page: page number
    """
    response = await client.get(page_url_template.format(developer_id, page), headers=headers)
    return response.json()