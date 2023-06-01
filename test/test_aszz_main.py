# include project root in sys path
import sys
import os
# insert at 1, 0 is the script path (or '' in REPL)
sys.path.insert(1, os.path.abspath("../"))

import argparse
import json
import logging as log
from time import time as ts
from typing import Dict
import yaml
import dateparser
from szz.aszz.a_szz import ASZZ
from szz.util.check_requirements import check_requirements

log.basicConfig(level=log.INFO, format='%(asctime)s :: %(funcName)s - %(levelname)s :: %(message)s')
log.getLogger('pydriller').setLevel(log.WARNING)

# krmoptic/snake - fix_commit_hash=ca119496290f4ba8594c1e298a77336825c71e77
oracle_bic = ['315a64b1bd627246b5a2c899ffdd47107d2b7fa6']

# function «void mv_snake(enum dir dir)» (line 83 - snake.c)
oracle_aszz_lines = {85, 86, 87, 88, 89, 90, 91, 92, 93, 94, 95, 96, 99, 100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110}


def main(input_json: str, out_json: str, conf: Dict, repos_dir: str):
    with open(input_json, 'r') as in_file:
        bugfix_commits = json.loads(in_file.read())

    tot = len(bugfix_commits)
    for i, commit in enumerate(bugfix_commits):
        bug_inducing_commits = set()
        repo_name = commit['repo_name']
        repo_url = f'https://test:test@github.com/{repo_name}.git'  # using test:test as git login to skip private repos during clone
        fix_commit = commit['fix_commit_hash']

        log.info(f'{i + 1} of {tot}: {repo_name} {fix_commit}')

        szz_name = conf['szz_name']
        if szz_name == 'a':
            a_szz = ASZZ(repo_full_name=repo_name, repo_url=repo_url, repos_dir=repos_dir)
            bug_inducing_commits = a_szz.start(fix_commit_hash=fix_commit, commit_issue_date=None, **conf)

            # test A-SZZ heuristic
            imp_files = a_szz.get_impacted_files(fix_commit, conf.get('file_ext_to_parse'), conf.get('only_deleted_lines'))
            new_imp_files = a_szz.process_added_lines(fix_commit, imp_files)
            aszz_lines = set(new_imp_files[0].modified_lines)
            assert len(aszz_lines - oracle_aszz_lines) == 0

        else:
            log.info(f'SZZ implementation not found: {szz_name}')
            exit(-3)

        log.info(f"result: {bug_inducing_commits}")
        found_bic = [bic.hexsha for bic in bug_inducing_commits if bic]
        #test found bic
        assert set(found_bic) == set(oracle_bic)

    log.info("+++ Test passed +++")


if __name__ == "__main__":
    check_requirements()

    parser = argparse.ArgumentParser(description='USAGE: python main.py <bugfix_commits.json> <conf_file path> <repos_directory(optional)>\n* If <repos_directory> is not set, pyszz will download each repository')
    parser.add_argument('input_json', type=str, help='/path/to/bug-fixes.json')
    parser.add_argument('conf_file', type=str, help='/path/to/configuration-file.yml')
    parser.add_argument('repos_dir', type=str, nargs='?', help='/path/to/repo-directory')
    args = parser.parse_args()

    if not os.path.isfile(args.input_json):
        log.error('invalid input json')
        exit(-2)
    if not os.path.isfile(args.conf_file):
        log.error('invalid conf file')
        exit(-2)

    with open(args.conf_file, 'r') as f:
        conf = yaml.safe_load(f)

    log.info(f"parsed conf yml: {conf}")
    szz_name = conf['szz_name']

    out_dir = 'out'
    if not os.path.isdir(out_dir):
        os.makedirs(out_dir)
    out_json = os.path.join(out_dir, f'bic_{szz_name}_{int(ts())}.json')

    if not szz_name:
        log.error('The configuration file does not define the SZZ name. Please, fix.')
        exit(-3)

    log.info(f'Launching {szz_name}-szz')

    main(args.input_json, out_json, conf, args.repos_dir)
