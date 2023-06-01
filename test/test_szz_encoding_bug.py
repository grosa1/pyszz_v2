# include project root in sys path
import sys
import os
# insert at 1, 0 is the script path (or '' in REPL)
sys.path.insert(1, os.path.abspath("../"))

import json
import logging as log
import os
import sys
from time import time as ts
from typing import Dict
import yaml

from szz.ma_szz import DetectLineMoved
from szz.r_szz import RSZZ

log.basicConfig(level=log.INFO, format='%(asctime)s :: %(levelname)s :: %(message)s')
log.getLogger('pydriller').setLevel(log.WARNING)


def main(input_json: str, out_json: str, conf: Dict, repos_dir: str):
    with open(input_json, 'r') as in_file:
        bugfix_commits = json.loads(in_file.read())

    tot = len(bugfix_commits)
    for commit in bugfix_commits:
        repo_name = commit['repo_name']
        repo_url = f'https://test:test@github.com/{repo_name}.git'
        fix_commit = commit['fix_commit_hash']

        log.info(f'{repo_name} {fix_commit}')

        szz_name = conf['szz_name']
        if szz_name == 'r':
            r_szz = RSZZ(repo_full_name=repo_name, repo_url=repo_url, repos_dir=repos_dir)
            imp_files = r_szz.get_impacted_files(fix_commit_hash=fix_commit, file_ext_to_parse=conf.get('file_ext_to_parse'), only_deleted_lines=conf.get('only_deleted_lines', True))
            bic_list = r_szz.find_bic(fix_commit_hash=fix_commit,
                                      impacted_files=imp_files,
                                      ignore_revs_file_path=conf.get('ignore_revs_file_path'),
                                      max_change_size=1000,
                                      detect_move_from_other_files=DetectLineMoved(conf.get('detect_move_from_other_files')))
            log.info(bic_list)
        else:
            log.info(f'SZZ implementation not found: {szz_name}')
            exit(-3)

        # assert [bic.hexsha for bic in bic_list][0] == oracle

    log.info("+++ Test passed +++")


if __name__ == "__main__":
    if len(sys.argv) < 4:
        print('USAGE: python main.py <bugfix_commits.json> <conf_file path> <repos_directory>')
        exit(-1)
    input_json = sys.argv[1]
    conf_file = sys.argv[2]
    repos_dir = sys.argv[3]

    if not os.path.isfile(input_json):
        log.error('invalid input json')
        exit(-2)
    if not os.path.isfile(conf_file):
        log.error('invalid conf file')
        exit(-2)

    with open(conf_file, 'r') as f:
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

    main(input_json, out_json, conf, repos_dir)
