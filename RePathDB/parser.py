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
from CGRtools.containers import ReactionContainer
from io import StringIO
from typing import Iterator

xyz = XYZRead(StringIO()).parse


def log_parser(file) -> Iterator[ReactionContainer]:
    """
    Check for header matching or raise error, returns parser
    """
    line = next(file)
    if line.startswith("Update the reaction path"):
        return pt_parser(file)
    else:
        raise ValueError


def pt_parser(file):
    """
        parser to work with specified file
    :return  tuple of 2 reaction containers. Each container consist of reactant(initaial state - mol container),
        product(final state - mol container), reagent(transition state - mol container). Each of mol containers
        should have {"energy":float} in meta dictionary.
    """
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
    mol1 = xyz(pts[0]['mol'])
    mol1.meta['energy'] = pts[0]['energy']
    mol1.meta['type'] = pts[0]['type']
    mol2 = xyz(pts[-1]['mol'])
    mol2.meta['energy'] = pts[-1]['energy']
    mol2.meta['type'] = pts[-1]['type']
    ts = xyz(structure['mol'])
    ts.meta['energy'] = structure['energy']
    ts.meta['type'] = structure['type']
    a = ReactionContainer(reagents=[ts], reactants=[mol1], products=[mol2])
    b = ReactionContainer(reagents=[ts], reactants=[mol2], products=[mol1])
    return a, b

