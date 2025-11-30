#!/usr/bin/env python -O
#
# Copyright (c) 2011-2016 Kyle Gorman, Max Bane, Morgan Sonderegger
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
# OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
# CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
# TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

from __future__ import print_function

import codecs
import re
from pathlib import Path

from .exceptions import TextGridError

DEFAULT_TEXTGRID_PRECISION = 5
DEFAULT_MLF_PRECISION = 5


def cmp(left, right):
    """Return negative if left < right, zero if equal, positive if left > right."""

    return (left > right) - (left < right)


def _getMark(text, short):
    """
    Return the mark or text entry on a line. Praat escapes double-quotes
    by doubling them, so doubled double-quotes are read as single
    double-quotes. Newlines within an entry are allowed.
    """

    line = text.readline()

    # check that the line begins with a valid entry type
    if not short and not re.match(r'^\s*(text|mark) = "', line):
        raise ValueError('Bad entry: ' + line)

    # read until the number of double-quotes is even
    while line.count('"') % 2:
        next_line = text.readline()

        if not next_line:
            raise EOFError('Bad entry: ' + line[:20] + '...')

        line += next_line
    if short:
        pattern = r'^"(.*?)"\s*$'
    else:
        pattern = r'^\s*(text|mark) = "(.*?)"\s*$'
    entry = re.match(pattern, line, re.DOTALL)

    return entry.groups()[-1].replace('""', '"')


def _formatMark(text):
    return text.replace('"', '""')


def detectEncoding(f):
    """
    This helper method returns the file encoding corresponding to path f.
    This handles UTF-8, which is itself an ASCII extension, so also ASCII.
    """
    encoding = 'ascii'
    try:
        with codecs.open(f, 'r', encoding='utf-16') as source:
            source.readline()  # Read one line to ensure correct encoding
    except UnicodeError:
        try:
            with codecs.open(
                f, 'r', encoding='utf-8-sig'
            ) as source:  # revised utf-8 to utf-8-sig for utf-8 with byte order mark (BOM)
                source.readline()  # Read one line to ensure correct encoding
        except UnicodeError:
            with codecs.open(f, 'r', encoding='ascii') as source:
                source.readline()  # Read one line to ensure correct encoding
        else:
            encoding = 'utf-8-sig'  # revised utf-8 to utf-8-sig for utf-8 with byte order mark (BOM)
    else:
        encoding = 'utf-16'

    return encoding


def decode(string):
    """
    Decode HTK's mangling of UTF-8 strings into something useful
    """
    # print(string)
    return string
    return string.decode('string_escape').decode('UTF-8')


def parse_line(line, short, to_round):
    line = line.strip()
    if short:
        if '"' in line:
            return line[1:-1]
        return round(float(line), to_round)
    if '"' in line:
        m = re.match(r'.+? = "(.*)"', line)
        return m.groups()[0]
    m = re.match(r'.+? = (.*)', line)
    return round(float(m.groups()[0]), to_round)


def parse_header(source):
    header = source.readline()  # header junk
    m = re.match(r'File type = "([\w ]+)"', header)
    if m is None or not m.groups()[0].startswith('ooTextFile'):
        raise TextGridError(
            'The file could not be parsed as a Praat text file as it is lacking a proper header.'
        )

    short = 'short' in m.groups()[0]
    file_type = parse_line(source.readline(), short, '')  # header junk
    source.readline()  # header junk
    return (file_type, short)


def compute_output_path(name, prefix):
    root = Path(name).stem
    return Path(prefix) / f'{root}.TextGrid'
