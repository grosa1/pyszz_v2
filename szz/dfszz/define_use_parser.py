import logging as log
from typing import Set, Dict, List

from bs4 import BeautifulSoup
from bs4.element import Tag


class DefUseParser:
    ASSIGN_OP = ['=', '*=', '/=', '%=', '+=', '-=', '&=', '^=', '|=', '<<=', '>>=']
    PREFIX_OP = ['++', '--']
    TAG_TO_PARSE = ['decl', 'expr']
    STRUCT_OP = ['.', '->']

    def __init__(self):
        self.__defs = dict()  # var_name -> line_id
        self.__def_lines = dict()  # line_id -> var_name
        self.__defuse_chain = dict()  # def_line_num -> list of use_line_num

    def __add_define(self, element):
        var_name = element.string
        if var_name:
            line_num = DefUseParser.parse_line_num(element)
            elem_id = DefUseParser.get_line_id(var_name, line_num)
            self.__defs[var_name] = elem_id
            self.__def_lines[elem_id] = var_name
            self.__defuse_chain[elem_id] = set()
        else:
            log.warning(f'skip invalid define node: {element}')

    def __add_use(self, element) -> bool:
        try:
            var_name = element.string
            if var_name:
                line_num = DefUseParser.parse_line_num(element)
                chain = self.__defuse_chain[self.__defs[var_name]]
                chain.add(line_num)
                self.__defuse_chain[self.__defs[var_name]] = chain
            else:
                log.warning(f'skip invalid use node: {element}')

            return True
        except KeyError:
            return False

    def __parse_struct(self, element):
        n_children = element.findChildren(recursive=False)
        for j in range(len(n_children)):
            c = DefUseParser.safe_list_get(n_children, j, None)
            c_prev = DefUseParser.safe_list_get(n_children, j-1, None)
            c_next = DefUseParser.safe_list_get(n_children, j+1, None)
            if c and c.name == 'operator' and c.string in DefUseParser.STRUCT_OP \
                    and c_prev and c_prev.name == 'name' \
                    and c_next and c_next.name == 'name':
                element.string = c_prev.string + c.string + c_next.string

        return element

    def compute_duc(self, ast_xml: str, raw_output: bool = False) -> List:
        """
        Compute Define-Use Chains for each function in the AST.
        """
        duc = list()

        # Parse XML from a file object
        soup = BeautifulSoup(ast_xml, features="lxml-xml")
        function_xml = soup.find_all("function")
        for f in function_xml:  # for each function
            duc_data_raw = self.__process_functions(f)

            if raw_output:
                duc_data = duc_data_raw
            else:
                duc_data = duc_data_raw.defuse_chain

            duc.append(duc_data)

        return duc

    def __process_functions(self, function_ast: Tag) -> 'DefUseData':
        """
        Build Define-Use chains from a function of an AST created with srcML. The xml will be loaded into
        BeautifulSoup first.

        :param function_ast: srcML AST

        :return: DefUseData class composed of:
            *def_lines* = line_id -> var_name, all the lines found that define a variable;
            *defuse_chain* = def_line_num -> list of use_line_num*, define-use chain found for each variable in defs.
        """

        self.__init__()

        # define nodes currently visited but not yet used by current variables (in current line). They will be added when
        # processing the next statement
        pending_define_nodes = list()
        pending_use_nodes = list()

        visited = set()

        names = function_ast.find_all('name')  # find all variable names
        for name in names:
            n_parent = name.parent  # find each parent node

            if n_parent and n_parent not in visited and n_parent.name in DefUseParser.TAG_TO_PARSE:
                visited.add(n_parent)
                p_children = n_parent.findChildren(recursive=False)  # find each child node containing variables

                # check if statement is changed to add pending use and define nodes
                if pending_define_nodes and p_children and DefUseParser.parse_line_num(pending_define_nodes[-1]) != DefUseParser.parse_line_num(p_children[-1]):
                    for d in pending_define_nodes:
                        self.__add_define(d)
                    pending_define_nodes = list()
                    for u in pending_use_nodes:
                        self.__add_use(u)
                    pending_use_nodes = list()

                for i in range(len(p_children)):
                    node = p_children[i]
                    n_prev = DefUseParser.safe_list_get(p_children, i-1, None)
                    n_next = DefUseParser.safe_list_get(p_children, i+1, None)

                    if not node.string:
                        node = self.__parse_struct(node)

                    if node.name == 'name':  # check if is a variable
                        if node.parent.name == 'decl':  # parse declaration statements
                            pending_define_nodes.append(node)
                        elif node.parent.name == 'expr':  # parse expression statements
                            # Check if is an assignment (re-define).
                            # case 1 - postfix operation: "int a = a + b;" or else "a++;"
                            # case 2 - prefix operation: "++a;"
                            if n_next and n_next.name == 'operator' and n_next.string in DefUseParser.ASSIGN_OP or \
                                    n_prev and n_prev.name == 'operator' and n_prev.string in DefUseParser.PREFIX_OP:
                                pending_define_nodes.append(node)
                            else:
                                res = self.__add_use(node)
                                if not res:  # define for current variable is still pending, wait for next statement
                                    pending_use_nodes.append(node)

        # add remaining pending_define_nodes
        for pd in pending_define_nodes:
            self.__add_define(pd)

        # remove empty defuse chains
        empty_keys = [k for k, v in self.__defuse_chain.items() if not v]
        for k in empty_keys:
            del self.__defuse_chain[k]

        return DefUseData(self.__def_lines, self.__defuse_chain)

    @staticmethod
    def safe_list_get(lst, idx, default):
        try:
            return lst[idx]
        except IndexError:
            return default

    @staticmethod
    def parse_line_num(element):
        try:
            return int(element.attrs.get("pos:end", None).split(':')[0])
        except AttributeError:
            return None

    @staticmethod
    def get_line_id(name, line_num) -> str:
        return f"{name}:{line_num}"


class DefUseData:
    def __init__(self, def_lines:  Dict[int, str], defuse_chain:  Dict[int, Set]):
        self.def_lines = def_lines
        self.defuse_chain = defuse_chain