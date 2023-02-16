import json
import tqdm

from pydriller import Repository

programmers = {}
count = 0

repopath = input() # i.e. https://github.com/ishepard/pydriller
for commit in Repository(repopath).traverse_commits():
  count += 1

for commit in tqdm.tqdm(Repository(repopath).traverse_commits(),
                        total=count):
    author_id = (commit.author.email, commit.author.name)
    programmers[author_id] = {"name": commit.author.name, "commits": {}}

    for file in commit.modified_files:
        if file.filename not in programmers[author_id]:
            programmers[author_id]["commits"][file.filename] = {"added": 0, "deleted": 0}
        programmers[author_id]["commits"][file.filename]["added"] += file.added_lines
        programmers[author_id]["commits"][file.filename]["deleted"] += file.deleted_lines

print(programmers)