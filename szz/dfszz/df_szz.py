import logging as log
import os
import traceback
from typing import List, Dict, Set

import networkx as nx
from git import Commit

from szz.core.abstract_szz import ImpactedFile, LineChangeType, DetectLineMoved
from szz.dfszz.define_use_parser import DefUseParser
from szz.ma_szz import MASZZ
from szz.r_szz import RSZZ
from szz.common.srcml_wrapper import SrcML

SUPPORTED_FILE_EXT = ['.c', '.h']


class DFSZZ(MASZZ):
    """
    Proof of concept implementation of DeFine-use SZZ.
    """

    def __init__(self, repo_full_name: str, repo_url: str, repos_dir: str = None):
        super().__init__(repo_full_name, repo_url, repos_dir)

    def start(self, fix_commit_hash: str, commit_issue_date, **kwargs) -> Set[Commit]:
        file_ext_to_parse = kwargs.get('file_ext_to_parse')
        only_deleted_lines = False
        ignore_revs_file_path = kwargs.get('ignore_revs_file_path')
        max_change_size = kwargs.get('max_change_size')
        issue_date_filter = kwargs.get('issue_date_filter')
        detect_move_within_file = kwargs.get('detect_move_within_file', None)
        use_rszz_heuristic = kwargs.get('use_rszz_heuristic', True)
        filter_revert_commits = kwargs.get('filter_revert_commits', False)

        detect_move_from_other_files = kwargs.get('detect_move_from_other_files', None)
        if detect_move_from_other_files:
            detect_move_from_other_files = DetectLineMoved(detect_move_from_other_files)

        assert kwargs.get('defuse_chain_radius') >= 0, "defuse_chain_radius param must be >= 0"
        distance_radius = kwargs['defuse_chain_radius']
        log.info("using def-use chain graph distance radius: {}".format(distance_radius))

        imp_files = self.get_impacted_files(fix_commit_hash, file_ext_to_parse, only_deleted_lines)

        # process impacted files with deleted lines
        imp_files_delete = [f for f in imp_files if f.line_change_type == LineChangeType.DELETE]
        bic_found = super().find_bic(fix_commit_hash=fix_commit_hash,
                                impacted_files=imp_files_delete,
                                ignore_revs_file_path=ignore_revs_file_path,
                                max_change_size=max_change_size,
                                detect_move_within_file=detect_move_within_file,
                                detect_move_from_other_files=detect_move_from_other_files,
                                issue_date_filter=issue_date_filter,
                                issue_date=commit_issue_date,
                                filter_revert_commits=filter_revert_commits)

        # process impacted files with added lines
        impacted_files_duchain = self._process_impacted_files(fix_commit_hash, imp_files, distance_radius)
        bic_found.update(super().find_bic(blame_rev_pointer='HEAD',
                                     fix_commit_hash=fix_commit_hash,
                                     impacted_files=impacted_files_duchain,
                                     ignore_revs_file_path=ignore_revs_file_path,
                                     max_change_size=max_change_size,
                                     detect_move_within_file=detect_move_within_file,
                                     detect_move_from_other_files=detect_move_from_other_files,
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

    def _process_impacted_files(self, fix_commit_hash: str, impacted_files: List['ImpactedFile'], cutoff_distance: int) -> List['ImpactedFile']:
        """
         Extract DefUseChains using added lines from impacted files.

        :param List['ImpactedFile'] impacted_files with the modified line ranges
        :returns List['ImpactedFile'] list of impacted files with lines selected with DefUseChains
        """

        def_use_imp_files = list()

        for imp_file in impacted_files:
            if imp_file.line_change_type == LineChangeType.ADD:
                if not os.path.splitext(imp_file.file_path)[-1] in SUPPORTED_FILE_EXT:
                    log.warning(f"skip file not supported by define-use chains parser: {imp_file.file_path}")
                    continue

                source_file_content = self.repository.git.show(f"{fix_commit_hash}:{imp_file.file_path}")
                ast_xml = SrcML().parse_file(imp_file.file_path, source_file_content)
                lines_to_blame = self._select_def_use_lines(imp_file, ast_xml, cutoff_distance)
                log.info(f"added lines to blame={lines_to_blame} for file={imp_file.file_path}")
                if lines_to_blame:
                    def_use_imp_files.append(ImpactedFile(imp_file.file_path, list(lines_to_blame), None))

        log.info(f"impacted_files_ext={def_use_imp_files}")

        return def_use_imp_files

    def _select_def_use_lines(self, imp_file: ImpactedFile, ast_xml: str, distance_radius: int) -> Set:
        """
        Compute the def-use chains at function level and select neighbor lines from impacted lines

        :param imp_file
        :param ast_xml
        :param distance_radius Include all neighbors of distance<=radius from n

        :return def_use_lines
        """

        def_use_lines = set()
        try:
            defuse_chains = DefUseParser().compute_duc(ast_xml=ast_xml)
            for du in defuse_chains:
                def_use_lines.update(DFSZZ.compute_neighbor_lines(du, imp_file.modified_lines, distance_radius))
        except:
            log.error(traceback.format_exc())

        return def_use_lines

    @staticmethod
    def compute_neighbor_lines(def_use_chains: Dict, modified_lines: List, distance_radius: int) -> Set:
        """
        Compute def-use neighbour lines of a list of impacted lines

        :param def_use_chains dict containing function-level define-use chains
        :param modified_lines
        :param distance_radius Include all neighbors of distance<=radius from n

        :return Set of selected neighbor_lines
        """

        neighbor_lines = set()
        G = DFSZZ.build_def_use_graph(def_use_chains)

        nodes = list(G.nodes)
        for i in range(len(nodes)):
            if nodes[i] in modified_lines:
                neighbor_lines.update(DFSZZ.select_neighbor_nodes(G, nodes[i], distance_radius))

        return neighbor_lines

    @staticmethod
    def build_def_use_graph(def_use_chains: Dict[str, List[int]]) -> nx.DiGraph:
        edges = set()
        for k in def_use_chains.keys():
            def_line = int(k.split(':')[1])
            for v in def_use_chains[k]:
                edges.add((def_line, v))

        G = nx.DiGraph()
        G.add_edges_from(edges)
        G.remove_edges_from(list(nx.selfloop_edges(G)))

        return G

    @staticmethod
    def select_neighbor_nodes(G: nx.DiGraph, node, distance_radius: int) -> Set:
        neighbor_lines = set()

        if distance_radius > 0:
            ego = nx.ego_graph(G, node, radius=distance_radius, center=True, undirected=False, distance=None)
        else:
            ego = nx.ego_graph(G, node, center=True, undirected=False, distance=None)
        neighbors = list(ego.nodes)
        if len(neighbors) > 1:  # there is at least one neighbor
            neighbors.remove(node)
            neighbor_lines.update(neighbors)
            log.info(f'neighbors={neighbors}')

        return neighbor_lines