import json
import logging as log
import os
import sys
import dateparser as dp
from typing import List

log.basicConfig(level=log.INFO, format='%(asctime)s :: %(funcName)s - %(levelname)s :: %(message)s')


if len(sys.argv) < 3:
    print("Usage: {} <results_folder> <repos_folder>".format(sys.argv[0]))
    sys.exit(1)

RESULTS_FOLDER = sys.argv[1]
REPOS_FOLDER = sys.argv[2]

SUFFIX = ".rszz.json"


class Commit:
    def __init__(self, hash: str, date: 'datatime'):
        self.hash = hash
        self.date = date


def get_committed_date(repo_full_name: str, commit: str) -> str:
    wd = os.getcwd()
    os.chdir(os.path.join(REPOS_FOLDER, repo_full_name))
    out = os.popen('git show -s --format=%cI "{}"'.format(commit)).read()
    os.chdir(wd)

    return out.strip()


def select_latest_commit(repo, bic) -> List[str]:
    bic_new = list()

    latest = Commit(None, None)
    for c in bic:
        commit_date = dp.parse(get_committed_date(repo, c))
        if not latest.date or commit_date > latest.date:
            latest = Commit(c, commit_date)
            log.info("Kept {} {}".format(c, commit_date.isoformat()))
        else:
            log.info("Filtered out {}".format(c, commit_date.isoformat()))
    if latest.hash:
        bic_new.append(latest.hash)

    return bic_new


def main():
    for f in os.listdir(RESULTS_FOLDER):
        if f.endswith(".json") and not f.endswith(SUFFIX):
            log.info(f)
            bugfix_commits_new = list()
            with open(os.path.join(RESULTS_FOLDER, f), "r") as infile:
                bugfix_commits = json.load(infile)
                for bfc in bugfix_commits:
                    log.info("Processing {} {}".format(bfc["repo_name"], bfc["fix_commit_hash"]))

                    repo_name = bfc["repo_name"]
                    bfc["inducing_commit_hash"] = select_latest_commit(repo_name, bfc["inducing_commit_hash"])
                    bugfix_commits_new.append(bfc)

            with open(os.path.join(RESULTS_FOLDER, f.replace(".json", SUFFIX)), "w") as outfile:
                json.dump(bugfix_commits_new, outfile)


if __name__ == "__main__":
    main()
    log.info("Done!")


