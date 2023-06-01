import logging as log
import os
import re
import subprocess
from collections import namedtuple
import tempfile

CommentRange = namedtuple('CommentRange', 'start end')
srcml_file_ext = ['.c', '.h', '.hh', '.hpp', '.hxx', '.cxx', '.cpp', '.cc', '.cs', '.java']


def parse_comments(file_str: str, file_name: str, temp_dir: str = tempfile.gettempdir()):
    if file_name.endswith(".py"):
        line_comment_ranges = py_comment_parser(file_str, file_name)
    elif file_name.endswith(".js"):
        line_comment_ranges = js_comment_parser(file_str, file_name)
    elif file_name.endswith(".php") or file_name.endswith(".phpt"):
        line_comment_ranges = php_comment_parser(file_str, file_name)
    elif file_name.endswith(".rb"):
        line_comment_ranges = rb_comment_parser(file_str, file_name)
    else:
        line_comment_ranges = parse_comments_srcml(file_str, file_name, temp_dir)

    return line_comment_ranges


def parse_comments_srcml(file_str: str, file_name: str, temp_folder: str = tempfile.gettempdir()):
    line_comment_ranges = list()

    if any(file_name.lower().endswith(e) for e in srcml_file_ext):
        if not os.path.isdir(temp_folder):
            os.makedirs(temp_folder)

        file_name = os.path.join(temp_folder, 'temp_' + file_name)
        with open(file_name, 'w') as temp_file:
            temp_file.write(file_str.encode('utf-8', 'replace').decode('utf-8'))

        process_out = list()
        p = subprocess.Popen(f'srcml --position {file_name}', shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        for line in p.stdout.readlines():
            process_out.append(line.decode('utf-8').strip())
        status = p.wait()

        if status == 0:
            for line in process_out:
                if line.strip().startswith("<comment"):
                    line_comment_ranges.append(CommentRange(start=int(re.search('pos:start="(\d+):', line).groups()[0]),
                                                            end=int(re.search('pos:end="(\d+):', line).groups()[0])))
        else:
            log.error(process_out)

        if os.path.isfile(file_name):
            os.remove(file_name)
    else:
        log.error(f"file not supported by srcML: {file_name}")

    return line_comment_ranges


def js_comment_parser(file_str, file_name):
    line_comment_ranges = list()

    if file_name.endswith(".js"):
        lines = file_str.splitlines()
        l_idx = 0
        while l_idx < len(lines):
            line = lines[l_idx].strip()
            if line.startswith("/*"):
                for i in range(l_idx, len(lines)):
                    line = lines[i].strip()
                    if i == l_idx:
                        line = line[2:]
                    if line and line.endswith("*/"):
                        line_comment_ranges.append(CommentRange(start=(l_idx + 1), end=(i + 1)))
                        l_idx = i
                        break
            elif line.startswith("//"):
                line_comment_ranges.append(CommentRange(start=(l_idx + 1), end=(l_idx + 1)))
            l_idx += 1
    else:
        log.error(f"unable to parse comments for: {file_name}")

    return line_comment_ranges


def php_comment_parser(file_str, file_name):
    line_comment_ranges = list()

    if file_name.endswith(".php"):
        lines = file_str.splitlines()
        l_idx = 0
        while l_idx < len(lines):
            line = lines[l_idx].strip()
            if line.startswith("/*"):
                for i in range(l_idx, len(lines)):
                    line = lines[i].strip()
                    if i == l_idx:
                        line = line[2:]
                    if line and line.endswith("*/"):
                        line_comment_ranges.append(CommentRange(start=(l_idx + 1), end=(i + 1)))
                        l_idx = i
                        break
            elif line.startswith("//") or line.startswith("#"):
                line_comment_ranges.append(CommentRange(start=(l_idx + 1), end=(l_idx + 1)))
            l_idx += 1
    else:
        log.error(f"unable to parse comments for: {file_name}")

    return line_comment_ranges


def rb_comment_parser(file_str, file_name):
    line_comment_ranges = list()

    if file_name.endswith(".rb"):
        lines = file_str.splitlines()
        l_idx = 0
        while l_idx < len(lines):
            line = lines[l_idx].strip()
            if line.startswith("=begin"):
                for i in range(l_idx, len(lines)):
                    line = lines[i].strip()
                    if line and line.endswith("=end"):
                        line_comment_ranges.append(CommentRange(start=(l_idx + 1), end=(i + 1)))
                        l_idx = i
                        break
            elif line.startswith("//") or line.startswith("#"):
                line_comment_ranges.append(CommentRange(start=(l_idx + 1), end=(l_idx + 1)))
            l_idx += 1
    else:
        log.error(f"unable to parse comments for: {file_name}")

    return line_comment_ranges


def py_comment_parser(file_str, file_name):
    line_comment_ranges = list()

    if file_name.endswith(".py"):
        lines = file_str.splitlines()
        l_idx = 0
        while l_idx < len(lines):
            line = lines[l_idx].strip()
            if line.startswith("'''") or line.startswith('"""'):
                for i in range(l_idx, len(lines)):
                    line = lines[i].strip()
                    if i == l_idx:
                        line = line[3:]
                    if line and (line.endswith("'''") or line.endswith('"""') or line.startswith("'''") or line.startswith('"""')):
                        line_comment_ranges.append(CommentRange(start=(l_idx + 1), end=(i + 1)))
                        l_idx = i
                        break
            elif line.startswith("#"):
                line_comment_ranges.append(CommentRange(start=(l_idx + 1), end=(l_idx + 1)))
            l_idx += 1
    else:
        log.error(f"unable to parse comments for: {file_name}")

    return line_comment_ranges
