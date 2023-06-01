import json
import logging as log
import os
import sys
from szz.l_szz import LSZZ
from typing import List

log.basicConfig(level=log.INFO, format='%(asctime)s :: %(funcName)s - %(levelname)s :: %(message)s')


if len(sys.argv) < 3:
    print("Usage: {} <results_folder> <repos_folder>".format(sys.argv[0]))
    sys.exit(1)

RESULTS_FOLDER = sys.argv[1]
REPOS_FOLDER = sys.argv[2]

SUFFIX = ".lszz.json"


def select_largest_commit(repo_name: str, bic: List[str]) -> List[str]:
    # using test:test as git login to skip private repos during clone
    repo_url = f'https://test:test@github.com/{repo_name}.git'

    szz = LSZZ(repo_name, repo_url, REPOS_FOLDER)
    bic = {szz.repository.commit(c) for c in bic}

    bic_new = list()
    largest = szz.select_largest_commit(bic)
    if largest:
        bic_new.append(largest.hexsha)

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
                    bfc["inducing_commit_hash"] = select_largest_commit(repo_name, bfc["inducing_commit_hash"])
                    bugfix_commits_new.append(bfc)

            with open(os.path.join(RESULTS_FOLDER, f.replace(".json", SUFFIX)), "w") as outfile:
                json.dump(bugfix_commits_new, outfile)


if __name__ == "__main__":
    main()
    log.info("Done!")


