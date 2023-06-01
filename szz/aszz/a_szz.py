import ntpath
from typing import List, Set
import logging as log
from git import Commit

from szz.aszz.code_block_parser import CodeBlockParser, CodeBlockRange
from szz.core.abstract_szz import ImpactedFile, LineChangeType
from szz.ma_szz import MASZZ
from szz.r_szz import RSZZ


class ASZZ(MASZZ):
    """
    A-SZZ implementation.

    Sahal, E., & Tosun, A. (2018, October). Identifying bug-inducing changes for code additions.
    In Proceedings of the 12th ACM/IEEE International Symposium on Empirical Software Engineering
    and Measurement (pp. 1-2).

    Supported **kwargs:
    TODO: add supported kwargs

    """

    def __init__(self, repo_full_name: str, repo_url: str, repos_dir: str = None):
        super().__init__(repo_full_name, repo_url, repos_dir)
        self.__enable_experimental = False

    def start(self, fix_commit_hash: str, commit_issue_date, **kwargs) -> Set[Commit]:
        self.__enable_experimental = kwargs.get('experimental', False)

        file_ext_to_parse = kwargs.get('file_ext_to_parse')
        only_deleted_lines = False
        ignore_revs_file_path = kwargs.get('ignore_revs_file_path')
        max_change_size = kwargs.get('max_change_size')
        issue_date_filter = kwargs.get('issue_date_filter')
        use_rszz_heuristic = kwargs.get('use_rszz_heuristic', True)
        filter_revert_commits = kwargs.get('filter_revert_commits', False)

        imp_files = self.get_impacted_files(fix_commit_hash, file_ext_to_parse, only_deleted_lines)

        imp_files_delete = [f for f in imp_files if f.line_change_type == LineChangeType.DELETE]
        bic_found = super().find_bic(fix_commit_hash=fix_commit_hash,
                                     impacted_files=imp_files_delete,
                                     ignore_revs_file_path=ignore_revs_file_path,
                                     max_change_size=max_change_size,
                                     issue_date_filter=issue_date_filter,
                                     issue_date=commit_issue_date,
                                     filter_revert_commits=filter_revert_commits)

        # process added lines
        imp_files_code_blocks = self.process_added_lines(fix_commit_hash, imp_files)
        bic_found.update(super().find_bic(blame_rev_pointer='HEAD',
                                     fix_commit_hash=fix_commit_hash,
                                     impacted_files=imp_files_code_blocks,
                                     ignore_revs_file_path=ignore_revs_file_path,
                                     max_change_size=max_change_size,
                                     issue_date_filter=issue_date_filter,
                                     issue_date=commit_issue_date,
                                     filter_revert_commits=filter_revert_commits))

        bic_found = {c for c in bic_found if c.hexsha != fix_commit_hash}

        if use_rszz_heuristic:
            log.info(f"bic_found={bic_found}")
            log.info(f"using R-SZZ heuristic...")
            return {RSZZ.select_latest_commit(bic_found)}
        else:
            return bic_found

    def process_added_lines(self, fix_commit_hash: str, impacted_files: List['ImpactedFile']) -> List['ImpactedFile']:
        """
        1. extract code blocks containing added lines
        2. select code blocks containing the added lines
        3. create an ImpactedFile containing the code block lines, without the added ones in the fix commit
        """
        new_imp_files = list()

        for imp_file in impacted_files:
            if imp_file.line_change_type == LineChangeType.ADD:
                source_file_content = self._get_impacted_file_content(fix_commit_hash, imp_file)
                code_blocks = self._parse_matching_code_blocks(imp_file.modified_lines, source_file_content, ntpath.basename(imp_file.file_path))
                log.info(f"found code_blocks={[f'{cb.start}-{cb.end}' for cb in code_blocks]} for file={imp_file.file_path}")

                lines_to_blame = set()
                for cb in code_blocks:
                    for l in range(cb.start, cb.end + 1):
                        if l not in imp_file.modified_lines:
                            lines_to_blame.add(l)
                log.info(f"added lines to blame={lines_to_blame} for file={imp_file.file_path}")
                if lines_to_blame:
                    new_imp_files.append(ImpactedFile(imp_file.file_path, list(lines_to_blame), None))

        log.info(f"new_imp_files={new_imp_files}")

        return new_imp_files

    def _parse_matching_code_blocks(self, lines_num: List, source_file_content: str, source_file_name: str) -> Set['CodeBlockRange']:
        """
        Extracts the code blocks line ranges containing the given lines - CodeBlockRange(start, end)

        :param List[int] lines_num: line number
        :param str source_file_content: The content of the file to parse
        :param str source_file_name: The name of the file to parse
        :returns bool
        """
        cb_ranges = CodeBlockParser().parse(source_file_content, source_file_name, self.__enable_experimental)

        matching_code_blocks = set()
        for line in lines_num:
            cb_temp = list()
            for cb in cb_ranges:
                if cb.start <= line <= cb.end:
                    if cb not in cb_temp and cb not in matching_code_blocks:
                        cb_temp.append(cb)
            if len(cb_temp) > 0:
                matching_code_blocks.add(cb_temp[-1])

        return matching_code_blocks
