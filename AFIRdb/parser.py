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
    is_ts = False
    is_pt = False
    for i in file:
        if i.startswith("Update the reaction path"):
            is_pt = True
        elif i.startswith("IRC"):
            is_ts = True
        break
    if is_ts:
        result = ts_parser(file)
        if len(result) == 3:
            for n, r in enumerate(result):
                if r.type == "TS":
                    tmp = n
                    break
            result.insert(0, result.pop(tmp))
            return result[0], result[1], result[2]
        else:
            raise ValueError
    elif is_pt:
        result = pt_parser(file)
        if len(result) == 3:
            for n, r in enumerate(result):
                if r.type == "PT":
                    tmp = n
                    break
            result.insert(0, result.pop(tmp))
            return result[0], result[1], result[2]
        else:
            raise ValueError


def pt_parser(file):
    structures = []
    pts = []
    tmp = []
    flag_struct = False
    flag_eq = False
    for i in file:
        if i[0] == "#":
            flag_struct = True
            if "EQ Converged" in i:
                flag_eq = True
            continue
        if flag_struct:
            if "Item" in i:
                continue
            if "ENERGY" in i:
                structure = {}
                structure["mol"] = xyz(tmp)
                structure["energy"] = float(i.split()[1])
                tmp = []
                if flag_eq:
                    structure["type"] = "EQ"
                    structure = log_data(structure['mol'], structure['energy'], structure['type'])
                    structures.append(structure)
                else:
                    structure["type"] = "PT"
                    pts.append(structure)
                flag_eq = False
                flag_struct = False
                continue
            at, x, y, z = i.split()
            tmp.append((at, float(x), float(y), float(z)))
    structure = sorted(pts, key=lambda x: x["energy"], reverse=True)[0]
    structure = log_data(structure['mol'], structure['energy'], structure['type'])
    structures.append(structure)
    return structures


def ts_parser(file):
    flag_ts = False
    flag_eq = False
    tmp = []
    structures = []
    for i in file:
        if flag_ts:
            if i.startswith("ENERGY"):
                flag_ts = False
                structure = {}
                structure["type"] = "TS"
                structure["mol"] = xyz(tmp)
                structure["energy"] = float(i.split()[2])
                tmp = []
                structure = log_data(structure['mol'], structure['energy'], structure['type'])
                structures.append(structure)
                continue
            at, x, y, z = i.split()
            tmp.append((at, float(x), float(y), float(z)))
        elif flag_eq:
            if i.startswith("ENERGY"):
                flag_eq = False
                structure = {}
                structure["type"] = "EQ"
                structure["mol"] = xyz(tmp)
                structure["energy"] = float(i.split()[2])
                tmp = []
                structure = log_data(structure['mol'], structure['energy'], structure['type'])
                structures.append(structure)
                continue
            at, x, y, z = i.split()
            tmp.append((at, float(x), float(y), float(z)))
        if i.startswith("INITIAL STRUCTURE"):
            flag_ts = True
        elif i.startswith("Optimized structure"):
            flag_eq = True
    return structures
