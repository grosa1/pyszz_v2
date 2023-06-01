import logging as log
from typing import Dict
from typing import Set

import dateparser as dp
from git import Commit


class IssueDateInfo():
    def __init__(self, source: str, parsed: 'datetime', date_tag: str):
        self.source = source
        self.parsed = parsed
        self.date_tag = date_tag

    def __repr__(self):
        return f"{self.__class__.__name__}(source_date={self.source},parsed_date={self.parsed},date_tag={self.date_tag}"


def parse_issue_date(commit: Dict) -> 'IssueDateInfo':
    """
    Reads iso date from commit and returns a MyIssueDate.
    Note: if the date is not timezone aware, it is assumed to be UTC.
    """

    source_date = None
    date_tag = None
    if 'earliest_issue_date' in commit:
        source_date = commit['earliest_issue_date']
        date_tag = 'earliest_issue_date'
    elif 'best_scenario_issue_date' in commit:
        source_date = commit['best_scenario_issue_date']
        date_tag = 'best_scenario_issue_date'

    assert source_date is not None, f'No issue date found in commit {commit}'
    assert date_tag is not None, f'Invalid date tag for commit {commit}'

    parsed_date = dp.parse(source_date)
    if not parsed_date.tzinfo:
        parsed_date = dp.parse(source_date + ' UTC')

    return IssueDateInfo(source_date, parsed_date, date_tag)


def filter_by_date(bic: Set[Commit], issue_date: 'IssueDateInfo') -> Set[Commit]:
    """ Filter commits by authored_date using timestamp of issue date (UTC) """

    bic_new = {commit for commit in bic if commit.authored_date < issue_date.parsed.timestamp()}
    log.info(f'Filtering by issue date returned {len(bic_new)} out of {len(bic)}')

    return bic_new
