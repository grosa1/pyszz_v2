#!/bin/bash

# preparing local test repo-directory
unzip repos_test_dfszz.zip

# executing DF-SZZ test (alt. implementation based on MA-SZZ)
python3 test_dfszz_ma_main.py bugfix_commits_dfszz_ma_test.json ../conf/dfszz_ma.yml repos_test_dfszz/

# cleanup
rm -rf repos_test_dfszz