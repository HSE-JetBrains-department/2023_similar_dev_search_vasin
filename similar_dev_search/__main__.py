import asyncio
from typing import List

import httpx
from tqdm import tqdm

from model import constants
from model.constants import max_candidates_num
from model.developer import Developer
from model.fetcher import fetch_stargazers_for_repo


async def get_candidates(start_developer: Developer, asyncio_client: httpx.AsyncClient = None) -> List[Developer]:
    """
    Return list of developers (candidates) from stargazers of stargazed repositories
    :param start_developer: developer, from whom to start looking for candidates
    :param asyncio_client: asyncio client to perform requests from
    :return:
    """
    developer_stargazes = await start_developer.get_stargazes(asyncio_client)
    tasks = []
    candidates = set[Developer]()
    if asyncio_client is None:
        client = httpx.AsyncClient(timeout=None)
    else:
        client = asyncio_client
    for repo in tqdm(developer_stargazes, total=len(developer_stargazes),
                     desc="gathering candidates from starred repos"):
        tasks.append(
            fetch_stargazers_for_repo(repo.url, client)
        )

    response = await asyncio.gather(*tasks)

    if asyncio_client is None:
        await client.aclose()

    for page_candidates in response:
        candidates.update([Developer(candidate_url) for candidate_url in page_candidates])

    return list(candidates)


if __name__ == '__main__':
    print('Enter github token:')
    token = input()
    constants.headers['Authorization'] = 'token ' + token

    print('Enter the github url of the developer, for which to find similar devs: ')
    starting_developer_url = input()
    starting_developer = Developer(starting_developer_url)

    repos = asyncio.run(starting_developer.get_repos())
    candidates = asyncio.run(get_candidates(starting_developer))
    print('Gathered', len(candidates), 'candidates, limiting to', max_candidates_num)