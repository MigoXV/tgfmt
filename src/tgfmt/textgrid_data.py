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

from .exceptions import TextGridError
from .interval import Interval
from .intervaltier import IntervalTier
from .point import Point
from .pointtier import PointTier
from .utils import (
    DEFAULT_TEXTGRID_PRECISION,
    _formatMark,
    _getMark,
    detectEncoding,
    parse_header,
    parse_line,
)


class TextGrid(object):
    """
    Represents Praat TextGrids as list of sequence types of tiers (e.g.,
    for tier in textgrid), and as map from names to tiers (e.g.,
    textgrid['tierName']). Whereas the *Tier classes that make up a
    TextGrid impose a strict ordering on Points/Intervals, a TextGrid
    instance is given order by the user. Like a true Python list, there
    are append/extend methods for a TextGrid.

    """

    def __init__(self, name=None, minTime=0., maxTime=None, strict=True):
        """
        Construct a TextGrid instance with the given (optional) name
        (which is only relevant for MLF stuff). If file is given, it is a
        string naming the location of a Praat-format TextGrid file from
        which to populate this instance.
        """
        self.name = name
        self.minTime = minTime
        self.maxTime = maxTime
        self.tiers = []
        self.strict = strict

    def __eq__(self, other):
        if not hasattr(other, 'tiers'):
            return False
        else:
            return all([a == b for a, b in zip(self.tiers, other.tiers)])

    def __str__(self):
        return '<TextGrid {0}, {1} Tiers>'.format(self.name, len(self))

    def __repr__(self):
        return 'TextGrid({0}, {1})'.format(self.name, self.tiers)

    def __iter__(self):
        return iter(self.tiers)

    def __len__(self):
        return len(self.tiers)

    def __getitem__(self, i):
        """
        Return the ith tier
        """
        return self.tiers[i]

    def getFirst(self, tierName):
        """
        Return the first tier with the given name.
        """
        for t in self.tiers:
            if t.name == tierName:
                return t

    def getList(self, tierName):
        """
        Return a list of all tiers with the given name.
        """
        tiers = []
        for t in self.tiers:
            if t.name == tierName:
                tiers.append(t)
        return tiers

    def getNames(self):
        """
        return a list of the names of the intervals contained in this
        TextGrid
        """
        return [tier.name for tier in self.tiers]

    def append(self, tier):
        if self.maxTime is not None and tier.maxTime is not None and tier.maxTime > self.maxTime:
            raise ValueError(self.maxTime)  # too late
        tier.strict = self.strict
        for i in tier:
            i.strict = self.strict
        self.tiers.append(tier)

    def extend(self, tiers):
        if min([t.minTime for t in tiers]) < self.minTime:
            raise ValueError(self.minTime)  # too early
        if self.maxTime and max([t.minTime for t in tiers]) > self.maxTime:
            raise ValueError(self.maxTime)  # too late
        self.tiers.extend(tiers)

    def pop(self, i=None):
        """
        Remove and return tier at index i (default last). Will raise
        IndexError if TextGrid is empty or index is out of range.
        """
        return (self.tiers.pop(i) if i else self.tiers.pop())

    def read(self, f, round_digits=DEFAULT_TEXTGRID_PRECISION, encoding=None):
        """
        Read the tiers contained in the Praat-formatted TextGrid file
        indicated by string f. Times are rounded to the specified precision.
        """
        if encoding is None:
            encoding = detectEncoding(f)
        with codecs.open(f, 'r', encoding=encoding) as source:
            file_type, short = parse_header(source)
            if file_type != 'TextGrid':
                raise TextGridError('The file could not be parsed as a TextGrid as it is lacking a proper header.')

            first_line_beside_header = source.readline()
            try:
                parse_line(first_line_beside_header, short, round_digits)
            except Exception:
                short = True

            self.minTime = parse_line(first_line_beside_header, short, round_digits)
            self.maxTime = parse_line(source.readline(), short, round_digits)
            source.readline()  # more header junk
            if short:
                m = int(source.readline().strip())  # will be self.n
            else:
                m = int(source.readline().strip().split()[2])  # will be self.n
            if not short:
                source.readline()
            for i in range(m):  # loop over grids
                if not short:
                    source.readline()
                if parse_line(source.readline(), short, round_digits) == 'IntervalTier':
                    inam = parse_line(source.readline(), short, round_digits)
                    imin = parse_line(source.readline(), short, round_digits)
                    imax = parse_line(source.readline(), short, round_digits)
                    itie = IntervalTier(inam, imin, imax)
                    itie.strict = self.strict
                    n = int(parse_line(source.readline(), short, round_digits))
                    for j in range(n):
                        if not short:
                            source.readline().rstrip().split()  # header junk
                        jmin = parse_line(source.readline(), short, round_digits)
                        jmax = parse_line(source.readline(), short, round_digits)
                        jmrk = _getMark(source, short)
                        if jmin < jmax:  # non-null
                            itie.addInterval(Interval(jmin, jmax, jmrk))
                    self.append(itie)
                else:  # pointTier
                    inam = parse_line(source.readline(), short, round_digits)
                    imin = parse_line(source.readline(), short, round_digits)
                    imax = parse_line(source.readline(), short, round_digits)
                    itie = PointTier(inam)
                    n = int(parse_line(source.readline(), short, round_digits))
                    for j in range(n):
                        source.readline().rstrip()  # header junk
                        jtim = parse_line(source.readline(), short, round_digits)
                        jmrk = _getMark(source, short)
                        itie.addPoint(Point(jtim, jmrk))
                    self.append(itie)

    def write(self, f, null=''):
        """
        Write the current state into a Praat-format TextGrid file. f may
        be a file object to write to, or a string naming a path to open
        for writing.
        """
        sink = f if hasattr(f, 'write') else codecs.open(f, 'w', 'UTF-8')
        print('File type = "ooTextFile"', file=sink)
        print('Object class = "TextGrid"\n', file=sink)
        print('xmin = {0}'.format(self.minTime), file=sink)
        # compute max time
        maxT = self.maxTime
        if not maxT:
            maxT = max([t.maxTime if t.maxTime else t[-1].maxTime \
                        for t in self.tiers])
        print('xmax = {0}'.format(maxT), file=sink)
        print('tiers? <exists>', file=sink)
        print('size = {0}'.format(len(self)), file=sink)
        print('item []:', file=sink)
        for (i, tier) in enumerate(self.tiers, 1):
            print('\titem [{0}]:'.format(i), file=sink)
            if tier.__class__ == IntervalTier:
                print('\t\tclass = "IntervalTier"', file=sink)
                print('\t\tname = "{0}"'.format(tier.name), file=sink)
                print('\t\txmin = {0}'.format(tier.minTime), file=sink)
                print('\t\txmax = {0}'.format(maxT), file=sink)
                # compute the number of intervals and make the empty ones
                output = tier._fillInTheGaps(null)
                print('\t\tintervals: size = {0}'.format(
                    len(output)), file=sink)
                for (j, interval) in enumerate(output, 1):
                    print('\t\t\tintervals [{0}]:'.format(j), file=sink)
                    print('\t\t\t\txmin = {0}'.format(
                        interval.minTime), file=sink)
                    print('\t\t\t\txmax = {0}'.format(
                        interval.maxTime), file=sink)
                    mark = _formatMark(interval.mark)
                    print('\t\t\t\ttext = "{0}"'.format(mark), file=sink)
            elif tier.__class__ == PointTier:  # PointTier
                print('\t\tclass = "TextTier"', file=sink)
                print('\t\tname = "{0}"'.format(tier.name), file=sink)
                print('\t\txmin = {0}'.format(tier.minTime), file=sink)
                print('\t\txmax = {0}'.format(maxT), file=sink)
                print('\t\tpoints: size = {0}'.format(len(tier)), file=sink)
                for (k, point) in enumerate(tier, 1):
                    print('\t\t\tpoints [{0}]:'.format(k), file=sink)
                    print('\t\t\t\ttime = {0}'.format(point.time), file=sink)
                    mark = _formatMark(point.mark)
                    print('\t\t\t\tmark = "{0}"'.format(mark), file=sink)
        sink.close()

    # alternative constructor

    @classmethod
    def fromFile(cls, f, name=None):
        tg = cls(name=name)
        tg.read(f)
        return tg
