#!/bin/bash

# preparing local repo-directory
unzip test/repos_test.zip -d test/

# executing MA-SZZ switching back to main pyszz directory
# in this case, the bug-fixes.json contains bugfix commits without issue date
python3 main.py test/bugfix_commits_test.json conf/maszz.yml test/repos_test/

# cleanup
rm -rf test/repos_test