import logging as log
import re
from typing import List

from szz.common.srcml_wrapper import SrcML


class CodeBlockParser:

    def __init__(self):
        # No args constructor
        pass

    #todo: add js code block parser
    def parse(self, file_str: str, file_name: str, experimental: bool = False) -> List:
        if experimental:
            if file_name.endswith(".py"):
                return self._parse_code_blocks_py(file_str)
            elif file_name.endswith(".php") or file_name.endswith(".phpt"):
                return self._parse_code_blocks_php(file_str)
            elif file_name.endswith(".rb"):
                return self._parse_code_blocks_rb(file_str)

        return self._parse_code_blocks_srcml(file_str, file_name)

    def _parse_code_blocks_srcml(self, file_str: str, file_name: str) -> List:
        code_block_ranges = list()

        process_out = SrcML().parse_file(file_name, file_str)
        if process_out:
            for line in process_out.splitlines():
                try:
                    if "<block_content" in line.strip():
                        block_pos = line.split("<block_content")[1]
                        start_pos = int(re.search(r'pos:start="(\d+):', block_pos).groups()[0])
                        end_pos = int(re.search(r'pos:end="(\d+):', block_pos).groups()[0])
                        code_block_ranges.append(CodeBlockRange(start=start_pos, end=end_pos))
                except AttributeError as e:
                    log.warning("Unable to parse code blocks for: {}".format(file_name))

        return code_block_ranges

    def _parse_code_blocks_py(self, file_str: str):
        """
        Experimental!
        """
        code_block_ranges = list()

        lines = file_str.splitlines()
        line_idx = 0
        while line_idx < len(lines):
            line = lines[line_idx]
            if 'if ' in line or 'for ' in line or 'while ' in line or 'def ' in line and ':' in line:
                block_ident = len(line) - len(line.lstrip())
                for i in range(line_idx, len(lines)):
                    line = lines[i]
                    line_ident = len(line) - len(line.lstrip())
                    if block_ident == line_ident:
                        code_block_ranges.append(CodeBlockRange(start=(line_idx + 1), end=(i + 1)))
                        line_idx = i
                        break

            line_idx += 1

        return code_block_ranges

    def _parse_code_blocks_rb(self, file_str: str):
        """
        Experimental!
        """
        code_block_ranges = list()

        lines = file_str.splitlines()
        line_idx = 0
        while line_idx < len(lines):
            line = lines[line_idx].strip()
            if 'if ' in line or 'unless ' in line or 'for ' in line or 'while ' in line or 'until ' in line or 'def ' in line:
                for i in range(line_idx, len(lines)):
                    line = lines[i].strip()
                    if line and line.endswith("end"):
                        code_block_ranges.append(CodeBlockRange(start=(line_idx + 1), end=(i + 1)))
                        line_idx = i
                        break

            line_idx += 1

        return code_block_ranges

    def _parse_code_blocks_php(self, file_str: str):
        """
        Experimental!
        TODO: check for ternary operator parsing
        """
        code_block_ranges = list()

        lines = file_str.splitlines()
        line_idx = 0
        while line_idx < len(lines):
            line = lines[line_idx].strip()
            if "{" in line and not '}' in line.strip().split('{', 1)[1]:
                    for i in range(line_idx, len(lines)):
                        line = lines[i].strip()
                        if line and line.endswith("}"):
                            code_block_ranges.append(CodeBlockRange(start=(line_idx + 1), end=(i + 1)))
                            line_idx = i
                            break
            elif 'for (' in line or 'if (' in line or 'while (' in line:
                if lines[line_idx + 1].startswith(' '):
                    line_idx += 1
                    code_block_ranges.append(CodeBlockRange(start=line_idx, end=(line_idx + 1)))

            line_idx += 1

        return code_block_ranges


class CodeBlockRange:
    def __init__(self, start: int, end: int):
        self.start = start
        self.end = end