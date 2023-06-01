#!/bin/bash

# preparing local test repo-directory
unzip repos_test_revert.zip

# executing revert commit filter test (DF-SZZ alt. implementation using R-SZZ heuristic)
python3 test_rszz_revert.py bugfix_commits_dfszz_revert.json ../conf/rszz+_test.yml repos_test_revert/

# cleanup
rm -rf repos_test_revert
