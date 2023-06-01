import logging as log
import os
import subprocess
import tempfile
import traceback
from pathlib import Path
from typing import List

from options import Options


class SrcML:
    """
    SrcML cli tool wrapper
    """

    def __init__(self, working_dir: str = Options.TEMP_WORKING_DIR):
        self.__working_dir = working_dir

    def __run(self, args: List[str] = list()) -> 'SrcMLOutput':
        """
        Execute SrcML cli tool. stderr is redirected to stdout.

        return: SrcMLOutput(exec_status, stdout)
        """

        status = None
        stdout = ''
        try:
            cmd = ['srcml'] + args
            p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            stdout, stderr = p.communicate()
            status = p.wait()

            stdout = stdout.decode('utf-8')
            if status != 0:
                raise Exception(stdout)
        except:
            log.error(traceback.format_exc())

        return SrcMLOutput(status, stdout)

    def __run_with_line_position(self, args: List[str] = None) -> 'SrcMLOutput':
        """
        Run SrcML cli tool with line position enabled
        """

        args.insert(0, '--position')

        return self.__run(args)

    def parse_file(self, input_file_name: str, input_file_str: str, line_pos: bool = True) -> str:
        """
        Parse a source file content with SrcML.

        return: AST XML string
        """

        ast_xml = ''

        with tempfile.TemporaryDirectory(dir=self.__working_dir) as tmpdirname:
            source_file = os.path.join(tmpdirname, input_file_name)
            Path(source_file).parent.absolute().mkdir(parents=True, exist_ok=True)

            with open(source_file, 'w') as temp_file:
                temp_file.write(input_file_str)

            args = [source_file]
            if line_pos:
                out = self.__run_with_line_position(args)
            else:
                out = self.__run(args)

            if out.exec_status == 0:
                ast_xml = out.stdout
            else:
                log.error(out.stdout)

        return ast_xml


class SrcMLOutput:
    def __init__(self, exec_status, stdout):
        self.exec_status = exec_status
        self.stdout = stdout
