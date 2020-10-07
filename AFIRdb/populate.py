# -*- coding: utf-8 -*-
#
#  Copyright 2020 Ramil Nugmanov <nougmanoff@protonmail.com>
#  Copyright 2020 Timur Gimadiev <timur.gimadiev@gmail.com>
#  This file is part of AFIRdb.
#
#  AFIRdb is free software; you can redistribute it and/or modify
#  it under the terms of the GNU Lesser General Public License as published by
#  the Free Software Foundation; either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#  GNU Lesser General Public License for more details.
#
#  You should have received a copy of the GNU Lesser General Public License
#  along with this program; if not, see <https://www.gnu.org/licenses/>.
#
from os import listdir
from os.path import join
from .graph import Reaction
from .parser import log_parser
from dash_html_components import Div
import codecs


def load_data(files, suffix):
    """
    method for console data upload
    :param files: path to directory
    :param suffix: file types to process
    updates databases
    """
    for f in sorted(listdir(files)):
        if not f.endswith(suffix):
            continue
        try:
            forward, backward = log_parser(open(join(files, f)))
        except ValueError:
            print(f'invalid: {f}')
            continue
        Reaction(forward)
        Reaction(backward)
        print(f'processed: {f}')

def load_one_file(file):
    """
    method for web interface data upload only one file. not used
    :param file:
    :return:
    """
    try:
        StreamReader = codecs.getreader('utf-8')  # here you pass the encoding
        wrapper_file = StreamReader(file)
        forward, backward = log_parser(wrapper_file)
    except ValueError:
        print(f'invalid: {file}')
        return "bad"
    Reaction(forward)
    Reaction(backward)
    print(f'processed: {file}')
    return "good"

def load_data_remotely(files): # old method for dash upload
    divs = []
    good = 0
    bad = 0
    for n, f in enumerate(files, start=1):
        try:
            StreamReader = codecs.getreader('utf-8')  # here you pass the encoding
            wrapper_file = StreamReader(f)
            forward, backward = log_parser(wrapper_file)
        except ValueError:
            print(f'invalid: {n}')
            bad += 1
            continue
        Reaction(forward)
        Reaction(backward)
        print(f'processed: {n}')
        good += 1
    else:
        divs.append(Div([
            '{} log files were processed and added to database, {} files were not processed due to errors,'
            ' not log files are omitted and were not taken into account'.format(good, bad)
        ]))
    return divs

__all__ = ['load_data']
