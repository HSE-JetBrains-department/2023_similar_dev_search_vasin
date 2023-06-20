import model.fetcher as fetcher


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
