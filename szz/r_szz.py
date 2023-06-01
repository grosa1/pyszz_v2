import logging as log
from operator import attrgetter
from typing import List, Set

from git import Commit

from szz.core.abstract_szz import ImpactedFile
from szz.ma_szz import MASZZ


class RSZZ(MASZZ):
    """
    Recent-SZZ implementation.

    Da Costa, D. A., McIntosh, S., Shang, W., Kulesza, U., Coelho, R., & Hassan, A. E. (2016). A framework for
    evaluating the results of the szz approach for identifying bug-introducing changes. IEEE Transactions on Software
    Engineering.

    Supported **kwargs:
    todo:
    """

    def __init__(self, repo_full_name: str, repo_url: str, repos_dir: str = None):
        super().__init__(repo_full_name, repo_url, repos_dir)

    # TODO: add parse and type check on kwargs
    def find_bic(self, fix_commit_hash: str, impacted_files: List['ImpactedFile'], **kwargs) -> Set[Commit]:
        bic_candidates = super().find_bic(fix_commit_hash, impacted_files, **kwargs)

        return {RSZZ.select_latest_commit(bic_candidates)}

    @staticmethod
    def select_latest_commit(bic_candidates: Set[Commit]) -> Commit:
        latest_bic = None
        if len(bic_candidates) > 0:
            latest_bic = max(bic_candidates, key=attrgetter('committed_date'))
            log.info(f"selected bug introducing commit: {latest_bic.hexsha}")

        return latest_bic
