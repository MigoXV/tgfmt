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
import logging
from bisect import bisect_left

from .exceptions import TextGridError
from .interval import Interval
from .utils import (
    DEFAULT_TEXTGRID_PRECISION,
    _getMark,
    detectEncoding,
    parse_header,
    parse_line,
)


class IntervalTier(object):
    """
    Represents Praat IntervalTiers as list of sequence types of Intervals
    (e.g., for interval in intervaltier). An IntervalTier is used much like a
    Python set in that it has add/remove methods, not append/extend methods.

    """

    def __init__(self, name=None, minTime=0., maxTime=None):
        self.name = name
        self.minTime = minTime
        self.maxTime = maxTime
        self.intervals = []
        self.strict = True

    def __eq__(self, other):
        if not hasattr(other, 'intervals'):
            return False
        else:
            return all([a == b for a, b in zip(self.intervals, other.intervals)])

    def __str__(self):
        return '<IntervalTier {0}, {1} intervals>'.format(self.name,
                                                          len(self))

    def __repr__(self):
        return 'IntervalTier({0}, {1})'.format(self.name, self.intervals)

    def __iter__(self):
        return iter(self.intervals)

    def __len__(self):
        return len(self.intervals)

    def __getitem__(self, i):
        return self.intervals[i]

    def add(self, minTime, maxTime, mark):
        interval = Interval(minTime, maxTime, mark)
        interval.strict = self.strict
        self.addInterval(interval)

    def addInterval(self, interval):
        if interval.minTime < self.minTime:  # too early
            raise ValueError(self.minTime)
        if self.maxTime and interval.maxTime > self.maxTime:  # too late
            # raise ValueError, self.maxTime
            raise ValueError(self.maxTime)
        i = bisect_left(self.intervals, interval)
        if i != len(self.intervals) and self.intervals[i] == interval:
            raise ValueError(self.intervals[i])
        interval.strict = self.strict
        self.intervals.insert(i, interval)

    def remove(self, minTime, maxTime, mark):
        self.removeInterval(Interval(minTime, maxTime, mark))

    def removeInterval(self, interval):
        self.intervals.remove(interval)

    def indexContaining(self, time):
        """
        Returns the index of the interval containing the given time point,
        or None if the time point is outside the bounds of this tier. The
        argument can be a numeric type, or a Point object.
        """
        i = bisect_left(self.intervals, time)
        if i != len(self.intervals):
            if self.intervals[i].minTime <= time <= \
                    self.intervals[i].maxTime:
                return i

    def intervalContaining(self, time):
        """
        Returns the interval containing the given time point, or None if
        the time point is outside the bounds of this tier. The argument
        can be a numeric type, or a Point object.
        """
        i = self.indexContaining(time)
        if i is not None:
            return self.intervals[i]

    def read(self, f, round_digits=DEFAULT_TEXTGRID_PRECISION):
        """
        Read the Intervals contained in the Praat-formated IntervalTier
        file indicated by string f
        """
        encoding = detectEncoding(f)
        with codecs.open(f, 'r', encoding=encoding) as source:
            file_type, short = parse_header(source)
            if file_type != 'IntervalTier':
                raise TextGridError('The file could not be parsed as a IntervalTier as it is lacking a proper header.')

            self.minTime = parse_line(source.readline(), short, round_digits)
            self.maxTime = parse_line(source.readline(), short, round_digits)
            n = int(parse_line(source.readline(), short, round_digits))
            for i in range(n):
                source.readline().rstrip()  # header
                imin = parse_line(source.readline(), short, round_digits)
                imax = parse_line(source.readline(), short, round_digits)
                imrk = _getMark(source, short)
                self.intervals.append(Interval(imin, imax, imrk))

    def _fillInTheGaps(self, null):
        """
        Returns a pseudo-IntervalTier with the temporal gaps filled in
        """
        prev_t = self.minTime
        output = []
        for interval in self.intervals:
            if prev_t < interval.minTime:
                output.append(Interval(prev_t, interval.minTime, null))
            output.append(interval)
            prev_t = interval.maxTime
        # last interval
        if self.maxTime is not None and prev_t < self.maxTime:  # also false if maxTime isn't defined
            output.append(Interval(prev_t, self.maxTime, null))
        return output

    def write(self, f, null=''):
        """
        Write the current state into a Praat-format IntervalTier file.

        Intervals are written without regard to sample alignment. It will
        then be up to the reader to detect whether an interval without
        samples may need to be added if sample alignment is desired.
        """
        sink = f if hasattr(f, 'write') else codecs.open(f, 'w', 'UTF-8')
        print('File type = "ooTextFile"', file=sink)
        print('Object class = "IntervalTier"\n', file=sink)

        print('xmin = {0}'.format(self.minTime), file=sink)
        print('xmax = {0}'.format(self.maxTime if self.maxTime \
                                      else self.intervals[-1].maxTime), file=sink)
        # compute the number of intervals and make the empty ones
        output = self._fillInTheGaps(null)
        # write it all out
        print('intervals: size = {0}'.format(len(output)), file=sink)
        for (i, interval) in enumerate(output, 1):
            print('intervals [{0}]:'.format(i), file=sink)
            print('\txmin = {0}'.format(interval.minTime), file=sink)
            print('\txmax = {0}'.format(interval.maxTime), file=sink)
            mark = interval.mark.replace('"', '""')
            print('\ttext = "{0}"'.format(mark), file=sink)
        sink.close()

    def bounds(self):
        return (self.minTime, self.maxTime or self.intervals[-1].maxTime)

    # alternative constructor

    @classmethod
    def fromFile(cls, f, name=None):
        it = cls(name=name)
        it.intervals = []
        it.read(f)
        return it
