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
from bisect import bisect_left

from .exceptions import TextGridError
from .point import Point
from .utils import (
    DEFAULT_TEXTGRID_PRECISION,
    _formatMark,
    _getMark,
    detectEncoding,
    parse_header,
    parse_line,
)


class PointTier(object):
    """
    Represents Praat PointTiers (also called TextTiers) as list of Points
    (e.g., for point in pointtier). A PointTier is used much like a Python
    set in that it has add/remove methods, not append/extend methods.

    """

    def __init__(self, name=None, minTime=0., maxTime=None):
        self.name = name
        self.minTime = minTime
        self.maxTime = maxTime
        self.points = []

    def __eq__(self, other):
        if not hasattr(other, 'points'):
            return False
        else:
            return all([a == b for a, b in zip(self.points, other.points)])

    def __str__(self):
        return '<PointTier {0}, {1} points>'.format(self.name, len(self))

    def __repr__(self):
        return 'PointTier({0}, {1})'.format(self.name, self.points)

    def __iter__(self):
        return iter(self.points)

    def __len__(self):
        return len(self.points)

    def __getitem__(self, i):
        return self.points[i]

    def add(self, time, mark):
        """
        constructs a Point and adds it to the PointTier, maintaining order
        """
        self.addPoint(Point(time, mark))

    def addPoint(self, point):
        if point < self.minTime:
            raise ValueError(self.minTime)  # too early
        if self.maxTime and point > self.maxTime:
            raise ValueError(self.maxTime)  # too late
        i = bisect_left(self.points, point)
        if i < len(self.points) and self.points[i].time == point.time:
            raise ValueError(point)  # we already got one right there
        self.points.insert(i, point)

    def remove(self, time, mark):
        """
        removes a constructed Point i from the PointTier
        """
        self.removePoint(Point(time, mark))

    def removePoint(self, point):
        self.points.remove(point)

    def read(self, f, round_digits=DEFAULT_TEXTGRID_PRECISION):
        """
        Read the Points contained in the Praat-formated PointTier/TextTier
        file indicated by string f
        """
        encoding = detectEncoding(f)
        with codecs.open(f, 'r', encoding=encoding) as source:
            file_type, short = parse_header(source)
            if file_type != 'TextTier':
                raise TextGridError('The file could not be parsed as a PointTier as it is lacking a proper header.')

            self.minTime = parse_line(source.readline(), short, round_digits)
            self.maxTime = parse_line(source.readline(), short, round_digits)
            n = int(parse_line(source.readline(), short, round_digits))
            for i in range(n):
                source.readline().rstrip()  # header
                itim = parse_line(source.readline(), short, round_digits)
                imrk = _getMark(source, short)
                self.points.append(Point(itim, imrk))

    def write(self, f):
        """
        Write the current state into a Praat-format PointTier/TextTier
        file. f may be a file object to write to, or a string naming a
        path for writing
       """
        sink = f if hasattr(f, 'write') else codecs.open(f, 'w', 'UTF-8')
        print('File type = "ooTextFile"', file=sink)
        print('Object class = "TextTier"\n', file=sink)

        print('xmin = {0}'.format(self.minTime), file=sink)
        print('xmax = {0}'.format(self.maxTime if self.maxTime \
                                      else self.points[-1].time), file=sink)
        print('points: size = {0}'.format(len(self)), file=sink)
        for (i, point) in enumerate(self.points, 1):
            print('points [{0}]:'.format(i), file=sink)
            print('\ttime = {0}'.format(point.time), file=sink)
            mark = _formatMark(point.mark)
            print('\tmark = "{0}"'.format(mark), file=sink)
        sink.close()

    def bounds(self):
        return (self.minTime, self.maxTime or self.points[-1].time)

    # alternative constructor

    @classmethod
    def fromFile(cls, f, name=None):
        pt = cls(name=name)
        pt.read(f)
        return pt
