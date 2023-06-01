#!/bin/bash

# preparing local test repo-directory
unzip repos_test.zip

# executing R-SZZ test
python3 test_rszz_main.py bugfix_commits_test.json ../conf/rszz.yml repos_test/

# cleanup
rm -rf repos_test