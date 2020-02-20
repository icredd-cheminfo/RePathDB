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
from CGRtools import XYZRead
from collections import namedtuple
from io import StringIO
from typing import List

xyz = XYZRead(StringIO()).from_xyz
log_data = namedtuple('Log', ['mol', 'energy', 'links', 'index'])


def log_parser(file) -> List[log_data]:
    result = []
    for i in get_blocks(file):
        result.append(parse(i))
    return result


def get_blocks(file):
    tmp = []
    blocks = []
    for i in file:
        if i[0] == "#":
            blocks.append(tmp)
            tmp = []
        tmp.append(i)
    else:
        blocks.append(tmp)
    return blocks[1:]


def parse(block):
    tmp = []
    counter = 0
    index = int(block[0].split()[4].rstrip(","))
    for n, i in enumerate(block[1:], start=1):
        if i.startswith("Energy"):
            mol = xyz(tmp)
            energy = float(i.split()[2])
            counter = n
            break
        at, x, y, z = i.split()
        tmp.append([at, float(x), float(y), float(z)])
    links = None
    for i in block[1+counter:]:
        if i.startswith("CONNECTION"):
            _, _, a, _, b = i.split()
            links = (a, b)

    return log_data(mol, energy, links, index)

