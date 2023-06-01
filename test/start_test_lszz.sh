#!/bin/bash

# preparing local test repo-directory
unzip repos_test.zip

# executing L-SZZ test
python3 test_lszz_main.py bugfix_commits_test.json ../conf/lszz.yml repos_test/

# cleanup
rm -rf repos_test