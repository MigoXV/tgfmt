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

import logging

from .utils import cmp


class Interval(object):
    """
    Represents an interval of time, with an associated textual mark, as
    stored in an IntervalTier.

    """

    def __init__(self, minTime, maxTime, mark):
        if minTime >= maxTime:
            # Praat does not support intervals with duration <= 0
            raise ValueError(minTime, maxTime)
        self.minTime = minTime
        self.maxTime = maxTime
        self.mark = mark
        self.strict = True

    def __repr__(self):
        return 'Interval({0}, {1}, {2})'.format(self.minTime, self.maxTime,
                                                self.mark if self.mark else None)

    def duration(self):
        """
        Returns the duration of the interval in seconds.
        """
        return self.maxTime - self.minTime

    def __lt__(self, other):
        if hasattr(other, 'minTime'):
            if self.strict and self.overlaps(other):
                raise (ValueError(self, other))
            elif self.overlaps(other):
                logging.warning("Overlap for interval %s: (%f, %f)",
                                self.mark, self.minTime, self.maxTime)
                return self.minTime < other.minTime
            return self.minTime < other.minTime
        elif hasattr(other, 'time'):
            return self.maxTime < other.time
        else:
            return self.maxTime < other

    def __gt__(self, other):
        if hasattr(other, 'maxTime'):
            if self.strict and self.overlaps(other):
                raise (ValueError(self, other))
            elif self.overlaps(other):
                logging.warning("Overlap for interval %s: (%f, %f)",
                                self.mark, self.minTime, self.maxTime)
                return self.minTime < other.minTime
            return self.maxTime > other.maxTime
        elif hasattr(other, 'time'):
            return self.minTime > other.time
        else:
            return self.minTime > other

    def __gte__(self, other):
        return self > other or self == other

    def __lte__(self, other):
        return self < other or self == other

    def __cmp__(self, other):
        if hasattr(other, 'minTime') and hasattr(other, 'maxTime'):
            if self.strict and self.overlaps(other):
                raise ValueError(self, other)
                # this returns the two intervals, so user can patch things
                # up if s/he so chooses
            elif self.overlaps(other):
                logging.warning("Overlap for interval %s: (%f, %f)",
                                self.mark, self.minTime, self.maxTime)
                return cmp(self.minTime, other.minTime)
            return cmp(self.minTime, other.minTime)
        elif hasattr(other, 'time'):  # comparing Intervals and Points
            return cmp(self.minTime, other.time) + \
                   cmp(self.maxTime, other.time)
        else:
            return cmp(self.minTime, other) + cmp(self.maxTime, other)

    def __eq__(self, other):
        """
        This might seem superfluous but not that a ValueError will be
        raised if you compare two intervals to each other...not anymore
        """
        if hasattr(other, 'minTime') and hasattr(other, 'maxTime'):
            if self.minTime == other.minTime:
                if self.maxTime == other.maxTime:
                    return True
        elif hasattr(other, 'time'):
            return self.minTime < other.time < self.maxTime
        else:
            return False

    def __iadd__(self, other):
        self.minTime += other
        self.maxTime += other

    def __isub__(self, other):
        self.minTime -= other
        self.maxTime -= other

    def overlaps(self, other):
        """
        Tests whether self overlaps with the given interval. Symmetric.
        See: http://www.rgrjr.com/emacs/overlap.html
        """
        return other.minTime < self.maxTime and \
               self.minTime < other.maxTime

    def __contains__(self, other):
        """
        Tests whether the given time point is contained in this interval,
        either a numeric type or a Point object.
        """
        if hasattr(other, 'minTime') and hasattr(other, 'maxTime'):
            return self.minTime <= other.minTime and \
                   other.maxTime <= self.maxTime
        elif hasattr(other, 'time'):
            return self.minTime <= other.time <= self.maxTime
        else:
            return self.minTime <= other <= self.maxTime

    def bounds(self):
        return (self.minTime, self.maxTime)
