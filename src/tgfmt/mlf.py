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

import re

from .intervaltier import IntervalTier
from .textgrid_data import TextGrid
from .utils import DEFAULT_MLF_PRECISION, compute_output_path, decode


class MLF(object):
    """
    Read in a HTK .mlf file generated with HVite -o SM and turn it into a
    list of TextGrids. The resulting class can be iterated over to give
    one TextGrid at a time, or the write(prefix='') class method can be
    used to write all the resulting TextGrids into separate files.

    Unlike other classes, this is always initialized from a text file.
    """

    def __init__(self, f, samplerate=10e6):
        self.grids = []
        self.read(f, samplerate)

    def __iter__(self):
        return iter(self.grids)

    def __str__(self):
        return '<MLF, {0} TextGrids>'.format(len(self))

    def __repr__(self):
        return 'MLF({0})'.format(self.grids)

    def __len__(self):
        return len(self.grids)

    def __getitem__(self, i):
        """
        Return the ith TextGrid
        """
        return self.grids[i]

    def read(self, f, samplerate, round_digits=DEFAULT_MLF_PRECISION):
        source = open(f, 'r')  # HTK returns ostensible ASCII

        source.readline()  # header
        while True:  # loop over text
            name = re.match('\"(.*)\"', source.readline().rstrip())
            if name:
                name = name.groups()[0]
                grid = TextGrid(name)
                phon = IntervalTier(name='phones')
                word = IntervalTier(name='words')
                wmrk = ''
                wsrt = 0.
                wend = 0.
                while 1:  # loop over the lines in each grid
                    line = source.readline().rstrip().split()
                    if len(line) == 4:  # word on this baby
                        pmin = round(float(line[0]) / samplerate, round_digits)
                        pmax = round(float(line[1]) / samplerate, round_digits)
                        if pmin == pmax:
                            raise ValueError('null duration interval')
                        phon.add(pmin, pmax, line[2])
                        if wmrk:
                            word.add(wsrt, wend, wmrk)
                        wmrk = decode(line[3])
                        wsrt = pmin
                        wend = pmax
                    elif len(line) == 3:  # just phone
                        pmin = round(float(line[0]) / samplerate, round_digits)
                        pmax = round(float(line[1]) / samplerate, round_digits)
                        if line[2] == 'sp' and pmin != pmax:
                            if wmrk:
                                word.add(wsrt, wend, wmrk)
                            wmrk = decode(line[2])
                            wsrt = pmin
                            wend = pmax
                        elif pmin != pmax:
                            phon.add(pmin, pmax, line[2])
                        wend = pmax
                    else:  # it's a period
                        word.add(wsrt, wend, wmrk)
                        self.grids.append(grid)
                        break
                grid.append(phon)
                grid.append(word)
            else:
                source.close()
                break

    def write(self, prefix=''):
        """
        Write the current state into Praat-formatted TextGrids. The
        filenames that the output is stored in are taken from the HTK
        label files. If a string argument is given, then the any prefix in
        the name of the label file (e.g., "mfc/myLabFile.lab"), it is
        truncated and files are written to the directory given by the
        prefix. An IOError will result if the folder does not exist.

        The number of TextGrids is returned.
        """
        for grid in self.grids:
            my_path = compute_output_path(grid.name, prefix)
            grid.write(open(my_path, 'w', encoding='UTF-8'))
        return len(self.grids)
