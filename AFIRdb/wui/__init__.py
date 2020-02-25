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
from base64 import encodebytes
from CGRtools import MoleculeContainer
from dash import Dash
from json import dumps
from os import getenv
from .plugins import external_scripts, external_stylesheets
from .layout import get_layout


MoleculeContainer._render_config['mapping'] = False
color_map = ['rgb(0,104,55)', 'rgb(26,152,80)', 'rgb(102,189,99)', 'rgb(166,217,106)', 'rgb(217,239,139)',
             'rgb(254,224,139)']


def svg2html(svg):
    return 'data:image/svg+xml;base64,' + encodebytes(svg.encode()).decode().replace('\n', '')


def get_sigma_graph(paths):
    nodes = []
    edges = []
    data = {'nodes': nodes, 'edges': edges}

    longest = max(len(x) for x, *_ in paths) - 1
    start = paths[0].nodes[0]
    target = paths[0].nodes[-1]
    nodes.append({'id': str(target.id), 'label': target.labels()[0],
                  'x': longest * 5, 'y': 0, 'size': 1, 'color': 'rgb(178,223,138)',
                  'structure': svg2html(target.depict())})
    nodes.append({'id': str(start.id), 'label': start.labels()[0],
                  'x': 0, 'y': 0, 'size': 1, 'color': 'rgb(178,223,138)',
                  'structure': svg2html(start.depict())})
    seen = {target.id, start.id}
    for r, (mol_rxn, costs, total) in enumerate(paths):
        for n, (x, c) in enumerate(zip(mol_rxn[1:-1], costs), start=1):
            if x.id not in seen:
                nodes.append({'id': str(x.id),
                              'label': f'{x.labels()[0]} ({c * 627.51:.1f})' if n % 2 else x.labels()[0],
                              'x': n * 5, 'y': r * 3, 'size': 1,
                              'color': 'rgb(253,191,111)' if n % 2 else 'rgb(178,223,138)',
                              'structure': svg2html(x.depict())})
                seen.add(x.id)

        for n, m in zip(mol_rxn, mol_rxn[1:]):
            try:
                color = color_map[r]
            except IndexError:
                color = color_map[-1]

            edges.append({'id': f'{r}-{n.id}-{m.id}', 'source': str(n.id), 'target': str(m.id),
                          'count': r * 5, 'color': color})
    return dumps(data)


dash = Dash(__name__, external_stylesheets=external_stylesheets, external_scripts=external_scripts)
dash.title = 'AFIRdb'
dash.layout = get_layout(dash)
dash.server.secret_key = getenv('SECRET_KEY', 'development')

'''
@dash.callback(Output('editor', 'upload'), [Input('editor', 'download')])
def standardise(value):
    if value:
        with BytesIO(value.encode()) as f, MRVread(f) as i:
            s = next(i)
        s = aam.transform([s])[0]
        with StringIO() as f:
            with MRVwrite(f) as o:
                o.write(s)
            value = f.getvalue()
    return value
'''

__all__ = ['dash']
