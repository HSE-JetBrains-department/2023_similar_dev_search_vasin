from collections import defaultdict
import requests
from pydriller import Repository
import tqdm


def get_top_from_stargazers(repo_url):
    url = f"https://api.github.com/repos/{repo_url.split('/')[-2]}/{repo_url.split('/')[-1]}"
    url += "/stargazers?page={}&per_page=100"
    stargazers = set()
    page = 1
    while True:
        response = requests.get(url.format(page)).json()

        if (len(response) == 0) or isinstance(response, dict):
            break
        stargazers.update(list(map(lambda user: user["login"], response)))
        page += 1

    url = "https://api.github.com/users/{}/starred?page={}&per_page=100"
    repo_url_feature = "html_url"
    starred_repos = defaultdict(int)
    for stargazer in stargazers:
        page = 1
        while True:
            response = requests.get(url.format(stargazer, page)).json()

            if (len(response) == 0) or isinstance(response, dict):
                break

            for repo in response:
                starred_repos[repo[repo_url_feature]] += 1

    return list(map(
        lambda repo: repo[0], sorted(starred_repos.items(), key=lambda it: it[1], reverse=True)
    ))[:100]


def get_programmers_info(repopath):
    programmers = {}

    for commit in tqdm.tqdm(Repository(repopath).traverse_commits()):
        programmers[commit.author.email] = {"name": commit.author.name, "commits": {}}

        for file in commit.modified_files:
            if file.filename not in programmers[commit.author.email]:
                programmers[commit.author.email]["commits"][file.filename] = {"added": 0, "deleted": 0}
            programmers[commit.author.email]["commits"][file.filename]["added"] += file.added_lines
            programmers[commit.author.email]["commits"][file.filename]["deleted"] += file.deleted_lines

    return programmers

repo = input()
print(get_top_from_stargazers(repo))
