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


def load_data(files, suffix):
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


__all__ = ['load_data']
