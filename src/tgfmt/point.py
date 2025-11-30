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
from .utils import cmp


class Point(object):
    """
    Represents a point in time with an associated textual mark, as stored
    in a PointTier.

    """

    def __init__(self, time, mark):
        self.time = time
        self.mark = mark

    def __repr__(self):
        return 'Point({0}, {1})'.format(self.time,
                                        self.mark if self.mark else None)

    def __lt__(self, other):
        if hasattr(other, 'time'):
            return self.time < other.time
        elif hasattr(other, 'minTime'):
            return self.time < other.minTime
        else:
            return self.time < other

    def __gt__(self, other):
        if hasattr(other, 'time'):
            return self.time > other.time
        elif hasattr(other, 'maxTime'):
            return self.time > other.maxTime
        else:
            return self.time > other

    def __eq__(self, other):
        if isinstance(other, Point):
            return self.time == other.time
        elif isinstance(other, Interval):
            return other.minTime < self.time < other.maxTime
        else:
            return self.time == other

    def __gte__(self, other):
        return self > other or self == other

    def __lte__(self, other):
        return self < other or self == other

    def __cmp__(self, other):
        """
        In addition to the obvious semantics, Point/Interval comparison is
        0 iff the point is inside the interval (non-inclusively), if you
        need inclusive membership, use Interval.__contains__
        """
        if hasattr(other, 'time'):
            return cmp(self.time, other.time)
        elif hasattr(other, 'minTime') and hasattr(other, 'maxTime'):
            return cmp(self.time, other.minTime) + \
                   cmp(self.time, other.maxTime)
        else:  # hopefully numerical
            return cmp(self.time, other)

    def __iadd__(self, other):
        self.time += other

    def __isub__(self, other):
        self.time -= other
