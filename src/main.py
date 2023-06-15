import asyncio
from typing import List

import httpx

from model import constants
from model.constants import max_candidates_num
from model.developer import Developer
from model.fetcher import fetch_stargazers_for_repo

from tqdm import tqdm


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


def compute_similarities(main_developer, developers) -> List[float]:
    """
    Get similarities between a developer and a list of others
    :param main_developer: base developer
    :param developers: other developers
    :return: list of similarities (cosine similarity based on languages and vars)
    """
    result = []
    i = 0
    for developer in tqdm(developers, desc='computing similarities between developers'):
        result.append(asyncio.run(main_developer.compute_similarity(developer)))
    return result

if __name__ == '__main__':
    print('Enter the github url of the developer, for which to find similar devs: ')
    starting_developer_url = input()
    starting_developer = Developer(starting_developer_url)

    repos = asyncio.run(starting_developer.get_repos())
    candidates = asyncio.run(get_candidates(starting_developer))
    print('Gathered', len(candidates), 'candidates, limiting to', max_candidates_num)
    candidates = candidates[0:min(len(candidates), max_candidates_num)]
    similarities = compute_similarities(starting_developer, candidates)
    print(similarities)
    sorted_devs = [developer for _, developer in sorted(zip(similarities, candidates), key=lambda x: x[0])]

    print('top developers similar to the given: ')
    for developer in sorted_devs:
        print(developer)
