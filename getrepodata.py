import asyncio
from collections import defaultdict

import tqdm
import pydriller
import httpx
import itertools

headers = {'Authorization': 'token '}


async def fetch_stargazer(client: httpx.AsyncClient, url, page):
    response = await client.get(url.format(page), headers=headers)
    # print(response.json())
    return response.json()


async def get_stargazers_for_page(url):
    stargazers = set()
    async with httpx.AsyncClient() as client:
        response = await asyncio.gather(
            *map(fetch_stargazer, itertools.repeat(client), itertools.repeat(url), list(range(1, stargazer_pages_num)))
        )
        for user in response:
            stargazers.update(list(map(lambda user: user["login"], user)))
    return stargazers


async def fetch_repos(client: httpx.AsyncClient, url, stargazer, page):
    # print(url.format(stargazer, page))
    response = await client.get(url.format(stargazer, page), headers=headers)
    # print(response.json())
    return response.json()


async def fetch_all_repos(url, stargazers):
    async with httpx.AsyncClient() as client:
        # TODO unhardcode pages_num
        repo_url_feature = "html_url"
        starred_repos = defaultdict(int)
        for stargazer_ind, stargazer in enumerate(stargazers):
            print('stargazer', stargazer_ind, 'out of', len(stargazers))
            response = await asyncio.gather(
                *map(fetch_repos, itertools.repeat(client), itertools.repeat(url), itertools.repeat(stargazer),
                     list(range(1, repos_pages_num)))
            )
            for repo in response[0]:
                # print('repo', repo, '\n\n\n')
                starred_repos[repo[repo_url_feature]] += 1
        return starred_repos


def get_top_from_stargazers(repo_url):
    org, name = repo_url.split('/')[-2:]
    url = f"https://api.github.com/repos/{org}/{name}"
    url += "/stargazers?page={}&per_page=100"
    loop = asyncio.get_event_loop()
    stargazers = loop.run_until_complete(get_stargazers_for_page(url))
    url = "https://api.github.com/users/{}/starred?page={}&per_page=100"
    loop = asyncio.get_event_loop()
    starred_repos = loop.run_until_complete(fetch_all_repos(url, stargazers))

    return list(map(
        lambda repo: repo[0], sorted(starred_repos.items(), key=lambda it: it[1], reverse=True)
    ))[:100]


def get_programmers_info(url):
    programmers = {}

    for commit in tqdm.tqdm(pydriller.Repository(url).traverse_commits()):
        programmers[commit.author.email] = {"name": commit.author.name, "commits": {}}

        for file in commit.modified_files:
            if file.filename not in programmers[commit.author.email]:
                programmers[commit.author.email]["commits"][file.filename] = {"added": 0, "deleted": 0}
            programmers[commit.author.email]["commits"][file.filename]["added"] += file.added_lines
            programmers[commit.author.email]["commits"][file.filename]["deleted"] += file.deleted_lines

    return programmers


stargazer_pages_num = 2
repos_pages_num = 10
repo = input('Repository url: ')
token = input('Github token: ')
headers['Authorization'] = 'token ' + token
print(get_top_from_stargazers(repo))
