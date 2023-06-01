import json
import logging as log
import os
import sys
from typing import List
import dateparser as dp
from szz.common.issue_date import parse_issue_date

log.basicConfig(level=log.INFO, format='%(asctime)s :: %(funcName)s - %(levelname)s :: %(message)s')


if len(sys.argv) < 3:
    print("Usage: {} <results_folder> <repos_folder>".format(sys.argv[0]))
    sys.exit(1)

RESULTS_FOLDER = sys.argv[1]
REPOS_FOLDER = sys.argv[2]

SUFFIX = ".issue-filter.json"


def get_authored_date(repo_full_name: str, commit: str) -> str:
    wd = os.getcwd()
    os.chdir(os.path.join(REPOS_FOLDER, repo_full_name))
    out = os.popen('git show -s --format=%aI "{}"'.format(commit)).read()
    os.chdir(wd)

    return out.strip()


def filter_by_issue_date(repo, issue_date, bic) -> List:
    bic_new = list()
    for c in bic:
        commit_date = dp.parse(get_authored_date(repo, c))
        if commit_date.timestamp() < issue_date.parsed.timestamp():
            bic_new.append(c)
            log.info("Kept {} {}".format(c, commit_date.isoformat()))
        else:
            log.info("Filtered out {}".format(c, commit_date.isoformat()))

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
                    assert not ("earliest_issue_date" in bfc and "best_scenario_issue_date" in bfc), "The json in {} contains both the earliest issue date and the best_scenario_issue_date".format(f)

                    issue_date = parse_issue_date(bfc)
                    log.info(issue_date)

                    bfc["inducing_commit_hash"] = filter_by_issue_date(bfc["repo_name"], issue_date, bfc["inducing_commit_hash"])
                    bugfix_commits_new.append(bfc)

            with open(os.path.join(RESULTS_FOLDER, f.replace(".json", SUFFIX)), "w") as outfile:
                json.dump(bugfix_commits_new, outfile)


if __name__ == "__main__":
    main()
    log.info("Done!")


