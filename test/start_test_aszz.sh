#!/bin/bash

# preparing local test repo-directory
unzip repos_test_dfszz.zip

# executing A-SZZ test
python3 test_aszz_main.py bugfix_commits_dfszz_test.json ../conf/aszz.yml repos_test_dfszz/

# cleanup
rm -rf repos_test_dfszz

# TODO: vadz/mahogany b0490673f557cbbd7c777f74fb84c3e05f529486

