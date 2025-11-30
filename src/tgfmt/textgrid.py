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

from .interval import Interval
from .intervaltier import IntervalTier
from .mlf import MLF
from .point import Point
from .pointtier import PointTier
from .textgrid_data import TextGrid
from .utils import (
    DEFAULT_MLF_PRECISION,
    DEFAULT_TEXTGRID_PRECISION,
    _formatMark,
    _getMark,
    cmp,
    compute_output_path,
    decode,
    detectEncoding,
    parse_header,
    parse_line,
)

__all__ = [
    'TextGrid',
    'MLF',
    'IntervalTier',
    'PointTier',
    'Interval',
    'Point',
    'cmp',
    '_getMark',
    '_formatMark',
    'detectEncoding',
    'decode',
    'parse_line',
    'parse_header',
    'DEFAULT_TEXTGRID_PRECISION',
    'DEFAULT_MLF_PRECISION',
    'compute_output_path',
]
