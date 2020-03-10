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
from typing import Tuple

xyz = XYZRead(StringIO()).from_xyz
log_data = namedtuple('Log', ['mol', 'energy', 'type'])


def log_parser(file) -> Tuple[log_data, log_data, log_data]:
    line = next(file)
    if line.startswith("Update the reaction path"):
        result = pt_parser(file)
        if len(result) == 3:
            return result
        else:
            raise ValueError

    else:
        raise ValueError


def pt_parser(file):
    pts = []
    tmp = []
    flag = False
    for i in file:
        if i[0] == "#":
            flag = True
            continue
        if flag:
            if "Item" in i:
                continue
            if "ENERGY" in i:
                structure = {}
                structure["mol"] = tmp
                structure["energy"] = float(i.split()[1])
                structure['type'] = "TMP"
                tmp = []
                pts.append(structure)
                flag = False
                continue
            at, x, y, z = i.split()
            tmp.append((at, float(x), float(y), float(z)))
    pts[0]["type"] = "EQ"
    pts[-1]["type"] = "EQ"
    if len(pts) < 3:
        raise ValueError
    structure = sorted(pts, key=lambda x: x["energy"], reverse=True)[0]
    if structure["type"] == "EQ":
        raise ValueError
    structure["type"] = "TS"
    structures = (log_data(xyz(structure['mol']), structure['energy'], structure['type']),
                  log_data(xyz(pts[0]['mol']), pts[0]['energy'], pts[0]['type']),
                  log_data(xyz(pts[-1]['mol']), pts[-1]['energy'], pts[-1]['type']))
    return structures

