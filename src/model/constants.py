headers = {'Authorization': 'token '}

print('Enter github token:')
token = input()

headers['Authorization'] = 'token ' + token
stargazer_pages_num = 2
repos_pages_num = 2

repos_limit = 4
max_candidates_num = 100
