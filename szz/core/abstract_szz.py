import logging as log
import ntpath
import os
from abc import ABC, abstractmethod
from enum import Enum
from shutil import copytree
from shutil import rmtree
from tempfile import mkdtemp
from typing import List, Set

from git import Commit, Repo
from pydriller import ModificationType, GitRepository as PyDrillerGitRepo

from options import Options
from szz.core.comment_parser import parse_comments


class AbstractSZZ(ABC):
    """
    AbstractSZZ is the base class for SZZ implementations. It has core methods for SZZ
    like blame and a diff parsing for impacted files. GitPython is used for base Git
    commands and PyDriller to parse commit modifications.
    """

    def __init__(self, repo_full_name: str, repo_url: str, repos_dir: str = None):
        """
        Init an abstract SZZ to use as base class for SZZ implementations.
        AbstractSZZ uses a temp folder to clone and interact with the given git repo, where
        the name of the repo folder will be the full name having '/' replaced with '_'.
        The init method also set the default_ignore_regex for modified lines.

        :param str repo_full_name: full name of the Git repository to clone and interact with
        :param str repo_url: url of the Git repository to clone
        :param str repos_dir: temp folder where to clone the given repo
        """
        self._repository = None

        os.makedirs(Options.TEMP_WORKING_DIR, exist_ok=True)
        self.__temp_dir = mkdtemp(dir=os.path.join(os.getcwd(), Options.TEMP_WORKING_DIR))
        self._repository_path = os.path.join(self.__temp_dir, repo_full_name.replace('/', '_'))
        if not os.path.isdir(self._repository_path):
            if repos_dir:
                repo_dir = os.path.join(repos_dir, repo_full_name)
                if os.path.isdir(repo_dir):
                    copytree(repo_dir, self._repository_path, symlinks=True)
                else:
                    log.error(f'unable to find local repository path: {repo_dir}')
                    exit(-4)
            else:
                log.info(f"Cloning repository {repo_full_name}...")
                Repo.clone_from(url=repo_url, to_path=self._repository_path)

        self._repository = Repo(self._repository_path)

    def __del__(self):
        log.info("cleanup objects...")
        self.__cleanup_repo()
        self.__clear_gitpython()

    @property
    def repository(self) -> Repo:
        """
         Getter of current GitPython Repo object.

         :returns git.Repo repository
        """
        return self._repository

    @property
    def repository_path(self) -> str:
        """
         Getter of current repository local path.

         :returns str repository_path
        """
        return self._repository_path

    @abstractmethod
    def find_bic(self, fix_commit_hash: str, impacted_files: List['ImpactedFile'], **kwargs) -> Set[Commit]:
        """
         Abstract main method to find bug introducing commits. To be implemented by the specific SZZ implementation.

        :param str fix_commit_hash: hash of fix commit to scan for buggy commits
        :param List[ImpactedFile] impacted_files: list of impacted files in fix commit
        :param **kwargs: optional parameters specific for each SZZ implementation
        :returns Set[Commit] a set of bug introducing commits candidates, represented by Commit object
        """
        pass

    def get_impacted_files(self, fix_commit_hash: str,
                           file_ext_to_parse: List[str] = None,
                           only_deleted_lines: bool = True) -> List['ImpactedFile']:
        """
         Parse the diff of given fix commit using PyDriller to obtain a list of ImpactedFile with
         impacted file path and modified line ranges. As default behaviour, all deleted lines in the diff which
         are also added are treated as modified lines.

        :param List[str] file_ext_to_parse: parse only the given file extensions
        :param only_deleted_lines: considers as modified lines only the line numbers that are deleted and added.
            By default, only deleted lines are considered
        :param str fix_commit_hash: hash of fix commit to parse
        :returns List[ImpactedFile] impacted_files
        """
        impacted_files = list()

        fix_commit = PyDrillerGitRepo(self.repository_path).get_commit(fix_commit_hash)
        for mod in fix_commit.modifications:
            # skip newly added files
            if not mod.old_path:
                continue

            # filter files by extension
            if file_ext_to_parse:
                ext = mod.filename.split('.')
                if len(ext) < 2 or (len(ext) > 1 and ext[1].lower() not in file_ext_to_parse):
                    log.info(f"skip file: {mod.filename}")
                    continue

            file_path = mod.new_path
            if mod.change_type == ModificationType.DELETE or mod.change_type == ModificationType.RENAME:
                file_path = mod.old_path

            lines_deleted = [deleted[0] for deleted in mod.diff_parsed['deleted']]
            if len(lines_deleted) > 0:
                impacted_files.append(ImpactedFile(file_path, lines_deleted, LineChangeType.DELETE))

            if not only_deleted_lines:
                lines_added = [added[0] for added in mod.diff_parsed['added']]
                if len(lines_added) > 0:
                    impacted_files.append(ImpactedFile(file_path, lines_added, LineChangeType.ADD))

        log.info(impacted_files)

        return impacted_files

    def _blame(self, rev: str,
               file_path: str,
               modified_lines: List[int],
               skip_comments: bool = False,
               ignore_revs_list: List[str] = None,
               ignore_revs_file_path: str = None,
               ignore_whitespaces: bool = False,
               detect_move_within_file: bool = False,
               detect_move_from_other_files: 'DetectLineMoved' = None
               ) -> Set['BlameData']:
        """
         Wrapper for Git blame command.

        :param str rev: commit revision
        :param str file_path: path of file to blame
        :param bool modified_lines: list of modified lines that will be converted in line ranges to be used with the param '-L' of git blame
        :param bool ignore_whitespaces: add param '-w' to git blame
        :param bool skip_comments: use a comment parser to identify and exclude line comments and block comments
        :param List[str] ignore_revs_list: specify a list of commits to ignore during blame
        :param bool detect_move_within_file: Detect moved or copied lines within a file
            (-M param of git blame, https://git-scm.com/docs/git-blame#Documentation/git-blame.txt--Mltnumgt)
        :param DetectLineMoved detect_move_from_other_files: Detect lines moved or copied from other files that were modified in the same commit
            (-C param of git blame, https://git-scm.com/docs/git-blame#Documentation/git-blame.txt--Cltnumgt)
        :param str ignore_revs_file_path: specify ignore revs file for git blame to ignore specific commits. The
            file must be in the same format as an fsck.skipList (https://git-scm.com/docs/git-blame)
        :returns Set[BlameData] a set of bug introducing commits candidates, represented by BlameData object
        """

        kwargs = dict()
        if ignore_whitespaces:
            kwargs['w'] = True
        if ignore_revs_file_path:
            kwargs['ignore-revs-file'] = ignore_revs_file_path
        if ignore_revs_list:
            kwargs['ignore-rev'] = list(ignore_revs_list)
        if detect_move_within_file:
            kwargs['M'] = True
        if detect_move_from_other_files and detect_move_from_other_files == DetectLineMoved.SAME_COMMIT:
            kwargs['C'] = True
        if detect_move_from_other_files and detect_move_from_other_files == DetectLineMoved.PARENT_COMMIT:
            kwargs['C'] = [True, True]
        if detect_move_from_other_files and detect_move_from_other_files == DetectLineMoved.ANY_COMMIT:
            kwargs['C'] = [True, True, True]

        bug_introd_commits = set()
        mod_line_ranges = self._parse_line_ranges(modified_lines)
        log.info(f"processing file: {file_path}")
        for entry in self.repository.blame_incremental(**kwargs, rev=rev, L=mod_line_ranges, file=file_path):
            # entry.linenos = input lines to blame (current lines)
            # entry.orig_lineno = output line numbers from blame (previous commit lines from blame)
            for line_num in entry.orig_linenos:
                source_file_content = self.repository.git.show(f"{entry.commit.hexsha}:{entry.orig_path}")
                line_str = source_file_content.split('\n')[line_num - 1].strip()
                b_data = BlameData(entry.commit, line_num, line_str, entry.orig_path)

                if skip_comments and self._is_comment(line_num, source_file_content, ntpath.basename(b_data.file_path)):
                    log.info(f"skip comment line ({line_num}): {line_str}")
                    continue

                log.info(b_data)
                bug_introd_commits.add(b_data)

        return bug_introd_commits

    def _parse_line_ranges(self, modified_lines: List) -> List[str]:
        """
        Convert impacted lines list to list of modified lines range. In case of single line,
        the range will be the same line as start and end - ['line_num, line_num', 'start, end', ...]

        :param str modified_lines: list of modified lines
        :returns List[str] impacted_lines_ranges
        """
        mod_line_ranges = list()

        if len(modified_lines) > 0:
            start = int(modified_lines[0])
            end = int(modified_lines[0])

            if len(modified_lines) == 1:
                return [f'{start},{end}']

            for i in range(1, len(modified_lines)):
                line = int(modified_lines[i])
                if line - end == 1:
                    end = line
                else:
                    mod_line_ranges.append(f'{start},{end}')
                    start = line
                    end = line

                if i == len(modified_lines) - 1:
                    mod_line_ranges.append(f'{start},{end}')

        return mod_line_ranges

    def _is_comment(self, line_num: int, source_file_content: str, source_file_name: str) -> bool:
        """
        Check if the given line is a comment. It uses a specific comment parser which returns the interval of line
        numbers containing comments - CommentRange(start, end)

        :param int line_num: line number
        :param str source_file_content: The content of the file to parse
        :param str source_file_name: The name of the file to parse
        :returns bool
        """

        comment_ranges = parse_comments(source_file_content, source_file_name, self.__temp_dir)

        for comment_range in comment_ranges:
            if comment_range.start <= line_num <= comment_range.end:
                return True
        return False

    def _set_working_tree_to_commit(self, commit: str):
        # self.repository.head.reference = self.repository.commit(fix_commit_hash)
        # reset the index and working tree to match the pointed-to commit
        self.repository.head.reset(commit=commit, index=True, working_tree=True)
        assert not self.repository.head.is_detached

    def _get_impacted_file_content(self, fix_commit_hash: str, impacted_file: 'ImpactedFile') -> str:
        return self.repository.git.show(f"{fix_commit_hash}:{impacted_file.file_path}")

    def get_commit(self, hash: str) -> Commit:
        """ return the Commit object for the given hash """
        return self.repository.commit(hash)

    def __cleanup_repo(self):
        """ Cleanup of local repository used by SZZ """
        if os.path.isdir(self.__temp_dir):
            rmtree(self.__temp_dir)

    def __clear_gitpython(self):
        """ Cleanup of GitPython due to memory problems """
        if self._repository:
            self._repository.close()
            self._repository.__del__()


class DetectLineMoved(Enum):
    """
    DetectLineMoved represents the -C param of git blame (https://git-scm.com/docs/git-blame#Documentation/git-blame.txt--Cltnumgt),
    which detect lines moved or copied from other files that were modified in the same commit. The default [<num>] param
    of alphanumeric characters to detect is used (i.e. 40).

    * SAME_COMMIT = -C
    * PARENT_COMMIT = -C -C
    * ANY_COMMIT = -C -C -C
    """
    SAME_COMMIT = 1
    PARENT_COMMIT = 2
    ANY_COMMIT = 3


class LineChangeType(Enum):
    """
    Git line change type

    * ADD = the line is only added
    * MODIFY = the line is deleted and then added
    * DELETE = the line is deleted, but also can be modified
    """
    ADD = 1
    MODIFY = 2
    DELETE = 3

class ImpactedFile:
    """ Data class to represent impacted files """
    def __init__(self, file_path: str, modified_lines: List[int], line_change_type: 'LineChangeType'):
        """
        :param str file_path: previous path of the current impacted file
        :param List[int] modified_lines: list of modified lines
        :param 'LineChangeType' line_change_type: the type of change performed in the modified lines
        :returns ImpactedFile
        """
        self.file_path = file_path
        self.modified_lines = modified_lines
        self.line_change_type = line_change_type

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}(file_path="{self.file_path}",modified_lines={self.modified_lines},line_change_type={self.line_change_type})'


class BlameData:
    """ Data class to represent blame data """
    def __init__(self, commit: Commit, line_num: int, line_str: str, file_path: str):
        """
        :param Commit commit: commit detected by git blame
        :param int line_num: number of the blamed line
        :param str line_str: content of the blamed line
        :param str file_path: path of the blamed file
        :returns BlameData
        """
        self.commit = commit
        self.line_num = line_num
        self.line_str = line_str
        self.file_path = file_path

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}(commit={self.commit.hexsha},line_num={self.line_num},file_path="{self.file_path}",line_str="{self.line_str}")'

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, self.__class__):
            return False
        return self.file_path == other.file_path and self.line_num == other.line_num

    def __hash__(self) -> int:
        return 31 * hash(self.line_num) + hash(self.file_path)
