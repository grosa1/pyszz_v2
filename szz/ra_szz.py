import json
import logging as log
import os
import tempfile
from typing import List, Set

from options import Options
from szz.ma_szz import MASZZ
from szz.core.abstract_szz import ImpactedFile, BlameData, DetectLineMoved


class RASZZ(MASZZ):
    """
    Refactoring Aware SZZ, improved version (RA-SZZ*). This version is based on Refactoring Miner 2.0.
    This is implemented at blame-level. It simply filters blame results by excluding lines that refer to refactoring
    operations detected by Refactoring Miner.

    Revisiting and improving szz implementations, in 2019 ACM/IEEE International Symposium on Empirical Software
    Engineering and Measurement (ESEM). IEEE, 2019, pp. 1–12.

    Supported **kwargs:
    todo:
    """

    def __init__(self, repo_full_name: str, repo_url: str, repos_dir: str = None):
        super().__init__(repo_full_name, repo_url, repos_dir)

    def _extract_refactorings(self, commits):
        PATH_TO_REFMINER = os.path.join(Options.PYSZZ_HOME, 'tools/RefactoringMiner-2.0/bin/RefactoringMiner')

        refactorings = dict()
        for commit in commits:
            if not commit in refactorings:
                with tempfile.NamedTemporaryFile(mode='r+') as tmpfile:
                    log.info(f'Running RefMiner on {commit}')
                    os.system(f'"{PATH_TO_REFMINER}" -c "{self._repository_path}" {commit} > {tmpfile.name}')
                    refactorings[commit] = json.loads(tmpfile.read())

        return refactorings

    def __read_refactorings_for_commit(self, fix_commit_hash, fix_refactorings):
        refactorings = list()
        try:
            refactorings = fix_refactorings[fix_commit_hash]['commits'][0]['refactorings']
        except (KeyError, IndexError) as e:
            # no refactorings found
            pass

        return refactorings

    def get_impacted_files(self, fix_commit_hash: str,
                           file_ext_to_parse: List[str] = None,
                           only_deleted_lines: bool = True) -> List['ImpactedFile']:
        impacted_files = set(super().get_impacted_files(fix_commit_hash, file_ext_to_parse, only_deleted_lines))

        fix_refactorings = self._extract_refactorings([fix_commit_hash])

        for refactoring in self.__read_refactorings_for_commit(fix_commit_hash, fix_refactorings):
            for location in refactoring['rightSideLocations']:
                file_path = location['filePath']
                from_line = location['startLine']
                to_line   = location['endLine']
                for f in impacted_files:
                    lines_to_remove = set()
                    for modified_line in f.modified_lines:
                        if file_path == f.file_path and modified_line >= from_line and modified_line <= to_line:
                            log.info(f'Ignoring {f.file_path} line {modified_line} (refactoring {refactoring["type"]})')
                            lines_to_remove.add(modified_line)
                    f.modified_lines = [line for line in f.modified_lines if not line in lines_to_remove]

        impacted_files = [f for f in impacted_files if len(f.modified_lines) > 0]
        return impacted_files

    def _blame(self,
               rev: str,
               file_path: str,
               modified_lines: List[int],
               skip_comments: bool = False,
               ignore_revs_list: List[str] = None,
               ignore_revs_file_path: str = None,
               ignore_whitespaces: bool = False,
               detect_move_within_file: bool = False,
               detect_move_from_other_files: 'DetectLineMoved' = None
               ) -> Set['BlameData']:

        log.info("Running super-blame")
        candidate_blame_data = super()._blame(
            rev,
            file_path,
            modified_lines,
            skip_comments,
            ignore_revs_list,
            ignore_revs_file_path,
            ignore_whitespaces,
            detect_move_within_file,
            detect_move_from_other_files
        )

        commits = set([blame.commit.hexsha for blame in candidate_blame_data])
        refactorings = self._extract_refactorings(commits)

        to_reblame = dict()
        result_blame_data = set()
        for blame in candidate_blame_data:
            can_add = True
            for refactoring in self.__read_refactorings_for_commit(blame.commit.hexsha, refactorings):
                for location in refactoring['rightSideLocations']:
                    file_path = location['filePath']
                    from_line = location['startLine']
                    to_line   = location['endLine']

                    if blame.file_path == file_path and blame.line_num >= from_line and blame.line_num <= to_line and blame.commit.hexsha not in ignore_revs_list:
                        log.info(f'Ignoring {blame.file_path} line {blame.line_num} (refactoring {refactoring["type"]})')
                        commit_key = blame.commit.hexsha + "@" + blame.file_path
                        if not commit_key in to_reblame:
                            to_reblame[commit_key] = ReblameCandidate(blame.commit.hexsha, blame.file_path, {blame.line_num})
                        else:
                            to_reblame[commit_key].modified_lines.add(blame.line_num)
                        can_add = False

            if can_add:
                result_blame_data.add(blame)

        for _, reblame_candidate in to_reblame.items():
            log.info(f'Re-blaming {reblame_candidate.file_path} @ {reblame_candidate.rev}, lines {reblame_candidate.modified_lines} because of refactoring')

            new_ignore_revs_list = ignore_revs_list.copy()
            new_ignore_revs_list.append(reblame_candidate.rev)

            new_blame_results = self._blame(
                reblame_candidate.rev,
                reblame_candidate.file_path,
                list(reblame_candidate.modified_lines),
                skip_comments,
                new_ignore_revs_list,
                ignore_revs_file_path,
                ignore_whitespaces,
                detect_move_within_file,
                detect_move_from_other_files
            )

            result_blame_data.update(new_blame_results)

        return result_blame_data


class ReblameCandidate:
    def __init__(self, rev, file_path, modified_lines: Set):
        self.rev = rev
        self.file_path = file_path
        self.modified_lines = modified_lines
