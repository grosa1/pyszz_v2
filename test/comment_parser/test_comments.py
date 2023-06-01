# include project root in sys path
import sys
import os
# insert at 1, 0 is the script path (or '' in REPL)
sys.path.insert(1, os.path.abspath("../../"))

from szz.core.abstract_szz import AbstractSZZ, ImpactedFile
from szz.core.comment_parser import parse_comments


""" test python comment parser """
source_file_name = 'test.py'

with open(source_file_name) as f:
    source_file_content = f.read()

for i, l in enumerate(source_file_content.split("\n")):
    print(i + 1, l)

comment_ranges = parse_comments(source_file_content, source_file_name)

# comment [start, end]
comments = [[2, 2], [5, 10], [11, 11], [14, 16], [18, 18], [19, 19], [20, 20], [24, 25]]

assert len(comments) == len(comment_ranges)
for comment_range, oracle in zip(comment_ranges, comments):
    print(comment_range)
    assert comment_range.start == oracle[0] and comment_range.end == oracle[1]


""" test js comment parser """
source_file_name = 'test.js'

with open(source_file_name) as f:
    source_file_content = f.read()

for i, l in enumerate(source_file_content.split("\n")):
    print(i + 1, l)

comment_ranges = parse_comments(source_file_content, source_file_name)

# comment [start, end]
comments = [[2, 3], [8, 8], [10, 13], [14, 14], [17, 17], [18, 18], [19, 19], [21, 24]]

assert len(comments) == len(comment_ranges)
for comment_range, oracle in zip(comment_ranges, comments):
    print(comment_range)
    assert comment_range.start == oracle[0] and comment_range.end == oracle[1]


""" test php comment parser """
source_file_name = 'test.php'

with open(source_file_name) as f:
    source_file_content = f.read()

for i, l in enumerate(source_file_content.split("\n")):
    print(i + 1, l)

comment_ranges = parse_comments(source_file_content, source_file_name)

# comment [start, end]
comments = [[2, 5], [8, 8], [12, 12], [13, 16], [17, 17], [18, 18], [23, 26]]

assert len(comments) == len(comment_ranges)
for comment_range, oracle in zip(comment_ranges, comments):
    print(comment_range)
    assert comment_range.start == oracle[0] and comment_range.end == oracle[1]


""" test rb comment parser """
source_file_name = 'test.rb'

with open(source_file_name) as f:
    source_file_content = f.read()

for i, l in enumerate(source_file_content.split("\n")):
    print(i + 1, l)

comment_ranges = parse_comments(source_file_content, source_file_name)

# comment [start, end]
comments = [[2, 2], [6, 15], [16, 16]]

assert len(comments) == len(comment_ranges)
for comment_range, oracle in zip(comment_ranges, comments):
    print(comment_range)
    assert comment_range.start == oracle[0] and comment_range.end == oracle[1]

print("+++ Test passed +++")