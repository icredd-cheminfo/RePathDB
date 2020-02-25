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
from CGRdb import Molecule as pMolecule
from CGRtools import MoleculeContainer, MRVRead, MRVWrite
from dash import Dash
from dash.dependencies import Input, Output, State
from itertools import product
from io import StringIO, BytesIO
from os import getenv
from pony.orm import db_session
from .layout import get_layout
from .plugins import external_scripts, external_stylesheets
from ..graph import Molecule
from plotly.graph_objects import Figure, Layout, Scatter


MoleculeContainer._render_config['mapping'] = False
color_map = ['rgb(0,104,55)', 'rgb(26,152,80)', 'rgb(102,189,99)', 'rgb(166,217,106)', 'rgb(217,239,139)',
             'rgb(254,224,139)']


def svg2html(svg):
    return 'data:image/svg+xml;base64,' + encodebytes(svg.encode()).decode().replace('\n', '')


dash = Dash(__name__, external_stylesheets=external_stylesheets, external_scripts=external_scripts)
dash.title = 'AFIRdb'
dash.layout = get_layout(dash)
dash.server.secret_key = getenv('SECRET_KEY', 'development')


@dash.callback([Output('editor', 'upload'), Output('table', 'data')], [Input('editor', 'download')])
def search(mrv):
    table = [{'reactant': 'No results', 'product': 'No results', 'reactant_structure': 'No results',
              'product_structure': 'No results'}]
    if mrv:
        with BytesIO(mrv.encode()) as f, MRVRead(f) as i:
            s = next(i)
        s.standardize()
        s.thiele()

        with StringIO() as f:
            with MRVWrite(f) as o:
                o.write(s)
            mrv = f.getvalue()
        if s.products and s.reactants:
            tmp = []
            with db_session:
                m1 = pMolecule.find_substructures(s.reactants[0])
                m2 = pMolecule.find_substructures(s.products[0])
                if m1 and m2:
                    m1 = m1.molecules(pagesize=5)
                    m2 = m2.molecules(pagesize=5)
                    for m in m1:
                        m.structure.implicify_hydrogens()
                    for m in m2:
                        m.structure.implicify_hydrogens()
                    for i, j in product((Molecule.nodes.get(cgrdb=m.id) for m in m1),
                                        (Molecule.nodes.get(cgrdb=m.id) for m in m2)):
                        if i.has_path(j):
                            tmp.append({'reactant': i.id, 'product': j.id,
                                        'reactant_structure': str(i.structure), 'product_structure': str(j.structure)})
            if tmp:
                table = tmp
    return mrv, table


@dash.callback([Output('reagent_img', 'src'), Output('product_img', 'src'), Output('paths-graph', 'figure')],
               [Input('table', 'selected_rows')], [State('table', 'data')])
def search(row_id, table):
    if not row_id:
        return '', '', Figure()

    row = table[row_id[0]]
    m1 = Molecule.get(row['reactant'])
    m2 = Molecule.get(row['product'])
    with db_session:
        s1 = svg2html(m1.depict())
        s2 = svg2html(m2.depict())

    paths = m1.get_effective_paths(m2, 5)
    longest = max(len(x) for x, *_ in paths) - 1
    start = paths[0].nodes[0]
    target = paths[0].nodes[-1]
    nodes = {target.id: (longest * 5, 0), start.id: (0, 0)}
    edges = []
    for r, (mol_rxn, costs, total) in enumerate(paths):
        for n, (x, c) in enumerate(zip(mol_rxn[1:-1], costs), start=1):
            if x.id not in nodes:
                nodes[x.id] = (n * 5, r * 3)

        for n in mol_rxn:
            edges.append(nodes[n.id])
        edges.append((None, None))

    edge_trace = Scatter(
        x=[x for x, _ in edges], y=[x for _, x in edges],
        line=dict(width=0.5, color='#888'),
        hoverinfo='none',
        mode='lines')

    node_trace = Scatter(
        x=[x for x, _ in nodes.values()], y=[x for _, x in nodes.values()],
        mode='markers',
        hoverinfo='text',
        marker=dict(
            showscale=True,
            # colorscale options
            # 'Greys' | 'YlGnBu' | 'Greens' | 'YlOrRd' | 'Bluered' | 'RdBu' |
            # 'Reds' | 'Blues' | 'Picnic' | 'Rainbow' | 'Portland' | 'Jet' |
            # 'Hot' | 'Blackbody' | 'Earth' | 'Electric' | 'Viridis' |
            colorscale='YlGnBu',
            reversescale=True,
            color=[],
            size=10,
            line_width=2))

    figure = Figure(data=[edge_trace, node_trace],
                    layout=Layout(
                        showlegend=False,
                        hovermode='closest',
                        margin=dict(b=20, l=5, r=5, t=40),
                        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False))
                    )
    return s1, s2, figure


__all__ = ['dash']
