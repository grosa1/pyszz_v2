import logging as log
from typing import List, Set
from time import time as ts
from git import Commit
from pydriller import RepositoryMining, ModificationType
from szz.common.issue_date import filter_by_date
from szz.ag_szz import AGSZZ
from szz.core.abstract_szz import ImpactedFile, DetectLineMoved


class MASZZ(AGSZZ):
    """
    Meta-Change-Aware-SZZ implementation.

    T. Zimmermann, S. Kim, A. Zeller, and E. J. White- head Jr, “Mining version archives for co-changed lines.
    technical report”. 2006.

    Supported **kwargs:
    todo:
    """

    DEFAULT_MAX_CHANGE_SIZE = 20

    def __init__(self, repo_full_name: str, repo_url: str, repos_dir: str = None):
        super().__init__(repo_full_name, repo_url, repos_dir)
        self.__changes_to_ignore = [
            ModificationType.RENAME,
            ModificationType.COPY
        ]

    @property
    def change_types_to_ignore(self) -> List[ModificationType]:
        return self.__changes_to_ignore

    @change_types_to_ignore.setter
    def change_types_to_ignore(self, changes_to_ignore: List[ModificationType]):
        self.__changes_to_ignore = changes_to_ignore

    def _is_git_mode_change(self, git_show_output: List[str], current_file: str):
        return any(line.strip().startswith('mode change') and current_file in line for line in git_show_output)

    def select_meta_changes(self, commit_hash: str, current_file: str, filter_revert: bool = False) -> Set[str]:
        meta_changes = set()
        repo_mining = RepositoryMining(path_to_repo=self.repository_path, single=commit_hash).traverse_commits()
        for commit in repo_mining:
            # ignore revert commits
            if filter_revert and (commit.msg.startswith("Revert") or "This reverts commit" in commit.msg):
                log.info(f'exclude meta-change (Revert commit): {current_file} {commit.hash}')
                meta_changes.add(commit.hash)
                continue

            show_str = self.repository.git.show(commit.hash, '--summary').splitlines()
            if show_str and self._is_git_mode_change(show_str, current_file):
                log.info(f'exclude meta-change (file mode change): {current_file} {commit.hash}')
                meta_changes.add(commit.hash)
            else:
                try:
                    for m in commit.modifications:
                        if (current_file == m.new_path or current_file == m.old_path) and (m.change_type in self.change_types_to_ignore):
                            log.info(f'exclude meta-change ({m.change_type}): {current_file} {commit.hash}')
                            meta_changes.add(commit.hash)
                except Exception as e:
                    log.error(f'unable to analyze commit: {self.repository_path} {commit.hash}')

        return meta_changes

    def get_merge_commits(self, commit_hash: str) -> Set[str]:
        merge = set()
        repo_mining = RepositoryMining(single=commit_hash, path_to_repo=self.repository_path).traverse_commits()
        for commit in repo_mining:
            try:
                if commit.merge:
                    merge.add(commit.hash)
            except Exception as e:
                log.error(f'unable to analyze commit: {self.repository_path} {commit.hash}')

        if len(merge) > 0:
            log.info(f'merge commits count: {len(merge)}')

        return merge

    def find_bic(self, fix_commit_hash: str, impacted_files: List['ImpactedFile'], **kwargs) -> Set[Commit]:
        """
        Find bug introducing commits candidates.

        :param str fix_commit_hash: hash of fix commit to scan for buggy commits
        :param List[ImpactedFile] impacted_files: list of impacted files in fix commit
        :key ignore_revs_file_path (str): specify ignore revs file for git blame to ignore specific commits.
        :key max_change_size (int): if the number of modified files exceeds the threshold, the commit will be
            excluded (default 20)
        :key detect_move_from_other_files (DetectLineMoved): Detect lines moved or copied from other files that were
            modified in the same commit, from parent commits or from any commit (default DetectLineMoved.SAME_COMMIT)
        :returns Set[Commit] a set of bug introducing commits candidates, represented by Commit object
        """

        log.info(f"find_bic() kwargs: {kwargs}")
        self._set_working_tree_to_commit(fix_commit_hash)

        max_change_size = kwargs.get('max_change_size', MASZZ.DEFAULT_MAX_CHANGE_SIZE)
        filter_revert = kwargs.get('filter_revert_commits', False)

        params = dict()
        params['ignore_revs_file_path'] = kwargs.get('ignore_revs_file_path', None)
        params['detect_move_within_file'] = kwargs.get('detect_move_within_file', True)
        params['detect_move_from_other_files'] = kwargs.get('detect_move_from_other_files', DetectLineMoved.SAME_COMMIT)
        params['ignore_revs_list'] = list()
        if kwargs.get('blame_rev_pointer', None):
            params['rev_pointer'] = kwargs['blame_rev_pointer']

        log.info("staring blame")
        start = ts()
        blame_data = list()
        commits_to_ignore = set()
        commits_to_ignore_current_file = set()
        bic = set()
        for imp_file in impacted_files:
            commits_to_ignore_current_file = commits_to_ignore.copy()

            to_blame = True
            while to_blame:
                log.info(f"excluding commits: {params['ignore_revs_list']}")
                blame_data = self._ag_annotate([imp_file], **params)

                new_commits_to_ignore = set()
                new_commits_to_ignore_current_file = set()
                for bd in blame_data:
                    if bd.commit.hexsha not in new_commits_to_ignore and bd.commit.hexsha not in new_commits_to_ignore_current_file:
                        if bd.commit.hexsha not in commits_to_ignore_current_file:
                            new_commits_to_ignore.update(self._exclude_commits_by_change_size(bd.commit.hexsha, max_change_size=max_change_size))
                            new_commits_to_ignore.update(self.get_merge_commits(bd.commit.hexsha))
                            new_commits_to_ignore_current_file.update(self.select_meta_changes(bd.commit.hexsha, bd.file_path, filter_revert))

                if len(new_commits_to_ignore) == 0 and len(new_commits_to_ignore_current_file) == 0:
                    to_blame = False
                elif ts() - start > (60 * 60 * 1):  # 1 hour max time
                    log.error(f"blame timeout for {self.repository_path}")
                    to_blame = False

                commits_to_ignore.update(new_commits_to_ignore)
                commits_to_ignore_current_file.update(commits_to_ignore)
                commits_to_ignore_current_file.update(new_commits_to_ignore_current_file)
                params['ignore_revs_list'] = list(commits_to_ignore_current_file)

            bic.update({bd.commit for bd in blame_data if bd.commit.hexsha not in self._exclude_commits_by_change_size(bd.commit.hexsha, max_change_size)})

        if kwargs.get('issue_date_filter', False):
            bic = filter_by_date(bic, kwargs['issue_date'])
        else:
            log.info("Not filtering by issue date.")

        return bic
