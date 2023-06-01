#!/bin/bash

# preparing local repo-directory
unzip test/repos_test_with_issues.zip -d test/

# executing R-SZZ switching back to main pyszz directory
# in this case, the bug-fixes.json contains bugfix commits considering issue date
# (to be enabled by setting "issue_date_filter: true" in R-SZZ config file)
python3 main.py test/bugfix_commits_with_issues_test.json conf/rszz_test.yml test/repos_test_with_issues/

# cleanup
rm -rf test/repos_test_with_issues