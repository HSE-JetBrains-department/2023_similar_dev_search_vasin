headers = {'Authorization': 'token '}

token = input('Github token: ')
headers['Authorization'] = 'token ' + token
stargazer_pages_num = 2
repos_pages_num = 2

repos_limit = 4
max_candidates_num = 100
