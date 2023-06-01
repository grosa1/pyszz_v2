#!/bin/bash

# preparing local test repo-directory
unzip repos_test_dfszz.zip

# executing DF-SZZ test
python3 test_dfszz_main.py bugfix_commits_dfszz_test.json ../conf/dfszz.yml repos_test_dfszz/

# cleanup
rm -rf repos_test_dfszz