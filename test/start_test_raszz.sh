#!/bin/bash

# preparing local test repo-directory
unzip repos_test_raszz.zip

# executing RA-SZZ test
python3 -u test_raszz_main.py ./bugfix_commits_raszz_test.json ../conf/raszz.yml ./repos_test_raszz/

# cleanup
rm -rf repos_test_raszz