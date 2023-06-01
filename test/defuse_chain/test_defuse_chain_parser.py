# include project root in sys path
import sys
import os
# insert at 1, 0 is the script path (or '' in REPL)
sys.path.insert(1, os.path.abspath("../../"))

from szz.dfszz.define_use_parser import DefUseParser
from os import path
from szz.common.srcml_wrapper import SrcML


def read_file_content(test_file_path: str) -> str:
    with open(test_file_path, "r") as f:
        return f.read()


def duc_c_test():
    test_file_path = "test_duc.c"

    oracle_def_lines = {
        "a:2": "a",
        "c:3": "c",
        "d:4": "d",
        "a:5": "a",
        "a:6": "a",
        "b:7": "b",
        "i:8": "i",
        "d:9": "d",
        "d:13": "d"
    }

    oracle_defuse_chain = {
        "c:3": {4, 6, 7},
        "a:5": {6},
        "a:6": {7, 18},
        "i:8": {8},
        "d:9": {12},
        "d:13": {14, 15, 16}
    }

    ast_xml = SrcML(working_dir=os.getcwd()).parse_file(path.basename(test_file_path), read_file_content(test_file_path))
    du_data = DefUseParser().compute_duc(ast_xml=ast_xml, raw_output=True)

    assert type(du_data) == list
    assert len(du_data) == 1

    du_data = du_data[0]

    assert du_data.def_lines == oracle_def_lines
    assert du_data.defuse_chain == oracle_defuse_chain


def duc_c_with_struct_test():
    test_file_path = "test_duc_struct.c"

    oracle_def_lines = {
        "argc:10": "argc",
        "person1:11": "person1",
        "c:12": "c",
        "person1.salary:15": "person1.salary",
        "person1.citNo:16": "person1.citNo",
        "person1.salary:16": "person1.salary",
        "b:17": "b"
    }

    oracle_defuse_chain = {
        "c:12": {17},
        "person1.salary:16": {17, 22},
        "b:17": {19, 20}
    }

    ast_xml = SrcML(working_dir=os.getcwd()).parse_file(path.basename(test_file_path), read_file_content(test_file_path))
    du_data = DefUseParser().compute_duc(ast_xml=ast_xml, raw_output=True)

    assert type(du_data) == list
    assert len(du_data) == 1

    du_data = du_data[0]

    assert du_data.def_lines == oracle_def_lines
    assert du_data.defuse_chain == oracle_defuse_chain


if __name__ == '__main__':
    duc_c_test()
    duc_c_with_struct_test()
    print("+++ Test passed +++")
