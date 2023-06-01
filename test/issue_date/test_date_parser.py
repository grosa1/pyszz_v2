# include project root in sys path
import sys
import os
# insert at 1, 0 is the script path (or '' in REPL)
sys.path.insert(1, os.path.abspath("../../"))

from szz.common.issue_date import parse_issue_date, filter_by_date
import pickle


""" Test date parser """

bugfix_commits = [
    {
        "id": 4,
        "repo_name": "ahobson/ruby-pcap",
        "fix_commit_hash": "0ad41d0684c2ec4c2a6b604f7aafbaf9f0459dcc",
        "bug_commit_hash": [
            "272f03ff3b5bf79829f80c2febd004904d64006e"
        ],
        "best_scenario_issue_date": "2011-06-01T04:05:04",
        "language": [
            "rb"
        ],
        "inducing_commit_hash": []
    },     {
        "id": 4,
        "repo_name": "ahobson/ruby-pcap",
        "fix_commit_hash": "0ad41d0684c2ec4c2a6b604f7aafbaf9f0459dcc",
        "bug_commit_hash": [
            "272f03ff3b5bf79829f80c2febd004904d64006e"
        ],
        "best_scenario_issue_date": "2011-05-31T21:05:04-07:00",
        "language": [
            "rb"
        ],
        "inducing_commit_hash": []
    }
]

bic = pickle.load(open("bic.pkl", "rb"))
print(bic)

for bc in bugfix_commits:
    print(bc)
    issue_date = parse_issue_date(bc)
    assert issue_date.parsed.timestamp() == 1306901104.0

    bic_new = filter_by_date(bic, issue_date)
    print(bic_new)
    assert bic_new == bic