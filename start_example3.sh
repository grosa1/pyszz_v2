#!/bin/bash

# executing B-SZZ switching back to main pyszz directory
# local repo-directory is not provided, thus in this case pyszz will download each repository
# issue date filter is actually disabled in bszz config file (it can be enabled by setting "issue_date_filter: true")
python3 main.py test/bugfix_commits_with_issues_test.json conf/bszz.yml