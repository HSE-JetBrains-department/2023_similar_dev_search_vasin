import asyncio
from typing import List

import click
import httpx
from tqdm import tqdm

from model import constants
from model.constants import MAX_CANDIDATES_NUM
from model.developer import Developer
from model.fetcher import fetch_stargazers_for_repo
from model.repository import Repository
from model.repository_aggregator import RepositoryAggregator


async def get_candidates(start_developer: Developer, asyncio_client: httpx.AsyncClient = None) -> List[Developer]:
    """
    Return list of developers (candidates) from stargazers of stargazed repositories
    :param start_developer: developer, from whom to start looking for candidates
    :param asyncio_client: asyncio client to perform requests from
    :return: list of developer candidates: those who stargazed the start_developer's repositories
    """
    stargazed_repos = await start_developer.get_stargazed_repos(asyncio_client)
    tasks = []
    candidates = set[Developer]()
    if asyncio_client is None:
        client = httpx.AsyncClient(timeout=None)
    else:
        client = asyncio_client
    for repo in tqdm(stargazed_repos, total=len(stargazed_repos),
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


@click.command()
@click.option('--candidates_count', default=100, help='Number of candidates.')
@click.option('--stargazer_pages', default=2, help='Number of pages to collect stargazers from.')
@click.option('--repo_pages', default=2, help='Number of pages for each developer to collect stargazed repos from.')
@click.option('--repo_limit', default=4, help='Number of repositories to analyze for each developer.')
@click.option('--top_repos_from_stargazers', default=100,
              help='Number of top repos from stargazers of the initial to analyze.')
@click.option('--commits_per_repo', default=5, help='Number of commits to analyze.')
@click.option('--print_popular_repos', is_flag=True)
def print_similar_developers(candidates_count, stargazer_pages, repo_pages, repo_limit, top_repos_from_stargazers,
                             commits_per_repo, print_popular_repos):
    constants.MAX_CANDIDATES_NUM = candidates_count
    constants.STARGAZER_PAGES_NUM = stargazer_pages
    constants.REPOS_PAGES_NUM = repo_pages
    constants.REPOS_LIMIT = repo_limit
    constants.N_REPOS_FROM_STARGAZERS = top_repos_from_stargazers
    constants.COMMITS_PER_REPO = commits_per_repo

    print('Enter github token:')
    token = input()
    constants.HEADERS['Authorization'] = 'token ' + token

    print('Enter the url of the starting github repo')
    starting_repo_url = input()
    aggregator = RepositoryAggregator(Repository(starting_repo_url))

    asyncio.run(aggregator.get_repos())

    if print_popular_repos:
        print(f"Most common repos for stargazers of {starting_repo_url}: \n{aggregator.top_repos.most_common()}")

    candidates = asyncio.run(aggregator.get_developers())
    print('Gathered', len(candidates), 'candidates, limiting to', MAX_CANDIDATES_NUM)

    for developer in candidates:
        print(developer)


if __name__ == '__main__':
    print_similar_developers()
