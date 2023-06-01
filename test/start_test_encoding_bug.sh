#!/bin/bash

# preparing local test repo-directory
unzip repos_test_encoding_bug.zip

# executing R-SZZ test
python3 test_szz_encoding_bug.py bugfix_commits_test_encoding_bug.json ../conf/rszz.yml repos_test_encoding_bug/

# cleanup
rm -rf repos_test_encoding_bug