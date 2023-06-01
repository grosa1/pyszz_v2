import logging as log
from pydriller import RepositoryMining
from typing import Set


def extract_revert_commits(repository_path: str, commit_hash: str, current_file: str) -> Set[str]:
    meta_changes = set()

    repo_mining = RepositoryMining(path_to_repo=repository_path, single=commit_hash).traverse_commits()
    for commit in repo_mining:
        if commit.msg.startswith("Revert") or "This reverts commit" in commit.msg:
            log.info(f'exclude meta-change (Revert commit): {current_file} {commit.hash}')
            meta_changes.add(commit.hash)

    return meta_changes