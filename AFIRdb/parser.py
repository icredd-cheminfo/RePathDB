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


log_data = namedtuple('Log', ['mol', 'energy', 'links'])


def log_parser(file) -> List[log_data]:
    ...


'''file format following:
some information (several lines that will be not parsed)
#  block start symbol
'''
def get_blocks(lines):
    tmp=[]
    blocks=[]
    for i in lines:
        if i[0]=="#":
            #print(i)
            blocks.append(tmp)
            tmp=[]
        tmp.append(i)
    else:
        blocks.append(tmp)
    return blocks[1:]


def get_ts(block, typ):
    ts={}
    atoms=[]
    tmp=[]
    xyz=""
    for n,i in enumerate(block[1:],start=1):
        if i[:6]=="Energy":
            atoms.extend(tmp)
            tmp=n
            break
        xyz+=i
        at,x,y,z=i.split()
        tmp.append(((n,at),(float(x),float(y),float(z))))
    ts["Atoms"]=atoms
    ts["Atoms_xyz"]=str(ts['Atoms'][-1][0][0])+"\n"+"\n"+xyz
    a,_,b=block[tmp].split()
    ts[a]=float(b)
    for i in block[::-1]:
        if i[:10]=="CONNECTION":
            a,_,b,_,c=i.split()
            ts[a]= (int(b),int(c))
    ts["NUM"]=int(block[0].split()[4].rstrip(","))
    ts["LABEL"]=typ+":"+str(ts["NUM"])
    return ts


def get_eq(block):
    eq={}
    atoms=[]
    tmp=[]
    xyz=""
    for n,i in enumerate(block[1:],start=1):
        if i[:6]=="Energy":
            atoms.extend(tmp)
            tmp=n
            break
        xyz+=i
        at,x,y,z=i.split()
        tmp.append(((n,at),(float(x),float(y),float(z))))
    eq["Atoms"]=atoms
    eq["Atoms_xyz"]=str(eq['Atoms'][-1][0][0])+"\n"+"\n"+xyz
    a,_,b=block[tmp].split()
    eq[a]=float(b)
    eq["NUM"]=int(block[0].split()[4].rstrip(","))
    return eq



def put_tss(parsed, nodes):
    with StringIO(parsed['Atoms_xyz']) as s, XYZRead(s) as f:
        mol = next(f)
        a, b = parsed["CONNECTION"]
        mol1 = nodes[a]
        mol2 = nodes[b].mol
    put_ts(mol, parsed["Energy"], nodes[a], nodes[b])



def put_structures(mols):
    nodes = {}
    for n, i in enumerate(mols):
        with StringIO(parsed['Atoms_xyz']) as s, XYZRead(s) as f:
            mol = next(f)
            nodes[n] = put_struct(i, i["Energy"])
    return nodes
