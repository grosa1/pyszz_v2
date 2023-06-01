# include project root in sys path
import sys
import os
# insert at 1, 0 is the script path (or '' in REPL)
sys.path.insert(1, os.path.abspath("../../"))

from os import path
from typing import List, Dict

import networkx as nx

from szz.dfszz.df_szz import DFSZZ
from szz.dfszz.define_use_parser import DefUseParser
from szz.common.srcml_wrapper import SrcML


def read_file_content(test_file_path: str) -> str:
    with open(test_file_path, "r") as f:
        return f.read()


def build_duc(test_file_path: str) -> Dict[str, List[int]]:
    ast_xml = SrcML(working_dir=os.getcwd()).parse_file(path.basename(test_file_path), read_file_content(test_file_path))
    duc = DefUseParser().compute_duc(ast_xml=ast_xml, raw_output=False)
    assert type(duc) == list

    return duc


def build_duc_graph_test():
    test_file_path = "test_duc.c"

    edges_oracle = [(3, 4), (3, 6), (3, 7), (5, 6), (6, 7), (6, 18), (8, 8), (9, 12), (13, 14), (13, 15), (13, 16)]
    du_graph_oracle = nx.DiGraph()
    du_graph_oracle.add_edges_from(edges_oracle)
    du_graph_oracle.remove_edges_from(list(nx.selfloop_edges(du_graph_oracle)))

    duc = build_duc(test_file_path)
    assert len(duc) == 1
    duc = duc[0]

    du_graph = DFSZZ.build_def_use_graph(duc)
    assert du_graph is not None
    assert type(du_graph) == nx.classes.digraph.DiGraph
    assert du_graph.nodes == du_graph_oracle.nodes
    assert du_graph.edges == du_graph_oracle.edges
    assert nx.is_isomorphic(du_graph, du_graph_oracle) is True


def select_lines_from_graph_test():
    test_file_path = "test_duc.c"

    test_added_lines_num = [6, 13]

    oracle_neighbors_node_6 = {7, 18}
    oracle_neighbors_node_13 = {14, 15, 16}
    oracle_neighbor_lines = oracle_neighbors_node_6.union(oracle_neighbors_node_13)

    duc = build_duc(test_file_path)
    assert len(duc) == 1
    duc = duc[0]

    du_graph = DFSZZ.build_def_use_graph(duc)
    assert du_graph is not None
    assert len(du_graph.nodes) > 0

    neighbor_nodes = DFSZZ.select_neighbor_nodes(du_graph, node=test_added_lines_num[0], distance_radius=0)
    assert neighbor_nodes == oracle_neighbors_node_6

    neighbor_nodes = DFSZZ.select_neighbor_nodes(du_graph, node=test_added_lines_num[1], distance_radius=0)
    assert neighbor_nodes == oracle_neighbors_node_13

    neighbor_lines = DFSZZ.compute_neighbor_lines(duc, test_added_lines_num, distance_radius=0)
    assert oracle_neighbor_lines == neighbor_lines


if __name__ == '__main__':
    build_duc_graph_test()
    select_lines_from_graph_test()
    print("+++ Test passed +++")