import logging as log
from typing import List, Set

from git import Commit
from pydriller.metrics.process.lines_count import LinesCount
from szz.core.abstract_szz import ImpactedFile
from szz.ma_szz import MASZZ


class LSZZ(MASZZ):
    """
    Large-SZZ implementation.

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
        """
        Find bug introducing commits candidates selecting the ones having the highest number of modified lines.
        """

        bic_candidates = super().find_bic(fix_commit_hash=fix_commit_hash, impacted_files=impacted_files, **kwargs)

        return {self.select_largest_commit(bic_candidates)}

    def select_largest_commit(self, bic_candidates: Set[Commit]) -> Commit:
        bic_candidate = None
        max_mod_lines = 0
        for commit in bic_candidates:
            lc = LinesCount(path_to_repo=self.repository_path, from_commit=commit.hexsha, to_commit=commit.hexsha).count()
            mod_lines_count = 0
            for k in lc.keys():
                mod_lines_count += lc.get(k)

            if mod_lines_count > max_mod_lines:
                max_mod_lines = mod_lines_count
                bic_candidate = commit

        return bic_candidate
