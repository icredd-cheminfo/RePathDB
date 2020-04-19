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
from dash import callback_context
from itertools import product
from io import StringIO, BytesIO
from os import getenv
from pony.orm import db_session
from .layout import get_layout, reactant_color, product_color, reaction_color, molecule_color
from .plugins import external_scripts, external_stylesheets
from ..graph import Molecule, Reaction, Complex
from plotly.graph_objects import Figure, Layout, Scatter
from .utilities import get_figure, get_3d


MoleculeContainer._render_config['mapping'] = False
color_map = ['rgb(0,104,55)', 'rgb(26,152,80)', 'rgb(102,189,99)', 'rgb(166,217,106)', 'rgb(217,239,139)',
             'rgb(254,224,139)']


def svg2html(svg):
    return 'data:image/svg+xml;base64,' + encodebytes(svg.encode()).decode().replace('\n', '')


dash = Dash(__name__, external_stylesheets=external_stylesheets, external_scripts=external_scripts)
dash.title = 'AFIRdb'
dash.layout = get_layout(dash)
dash.server.secret_key = getenv('SECRET_KEY', 'development')
paths = []

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


@dash.callback([Output('reagent_img', 'src'), Output('product_img', 'src'), Output('table2', 'data')],
               [Input('table', 'selected_rows')], [State('table', 'data')])
def graph(row_id, table):
    if not row_id:
        table = [{'reactant': 'No results', 'product': 'No results', 'reactant_structure': 'No results',
                  'product_structure': 'No results'}]
        return '', '', table

    row = table[row_id[0]]
    m1 = Molecule.get(row['reactant'])
    m2 = Molecule.get(row['product'])
    with db_session:
        s1 = svg2html(m1.depict())
        s2 = svg2html(m2.depict())
    max_path = 1
    #max_path_graph = max_path +1 # mols were not included
    paths = m1.get_effective_paths(m2, max_path)
    pairs = []
    for r, path in enumerate(paths):
        #print(path.nodes[0])
        #a = Complex.nodes.get(path.nodes[0])
        #b = Complex.nodes.get(path.nodes[-1])
        pairs.append({'reactant': path.nodes[0].id, 'product': path.nodes[-1].id,
                                        'reactant_structure': path.nodes[0].signature, 'product_structure': path.nodes[-1].signature})

    return s1, s2, pairs


@dash.callback([Output('reagent_img2', 'src'), Output('product_img2', 'src'), Output('paths-graph', 'figure'),
                Output('net', 'data'), Output('structure', 'value')],
               [Input('table2', 'selected_rows'), Input('paths-graph', 'clickData'), Input('net', 'selectedId')],
               [State('table2', 'data'), State('paths-graph', 'figure'), State('reagent_img2', 'src'),
                State('product_img2', 'src'), State('net', 'data'), State('structure', 'value')])
def graph(row_id2_inp, path_graph_click, netid, table2, path_graph_data, reagent_img2, product_img2, net_data, struct_d3):
    ctx = callback_context
    element_id = ctx.triggered[0]['prop_id'].split('.')[0]
    print(ctx.triggered[0])
    #print(row_id2_inp, path_graph_click, table2, path_graph_data, reagent_img2, product_img2, net_data, struct_d3)
    if element_id == 'table2' and not row_id2_inp:
        return reagent_img2, product_img2, path_graph_data, net_data, struct_d3

    elif element_id == 'table2' and row_id2_inp:
        row = table2[row_id2_inp[0]]
        m1 = Complex.get(row['reactant'])
        m2 = Complex.get(row['product'])
        b1 = m1.brutto.all()[0]
        b2 = m2.brutto.all()[0]
        if b1 == b2:
            graph_nodes = [{'id': str(x.id), 'color': "grey"} for x in b1.complexes.all()]
            graph_links = [{'source': r.reactant.all()[0].id, 'target':r.product.all()[0].id, 'color':"green"} for r in b1.reactions.all()]
            net_data = {'nodes': graph_nodes, 'links': graph_links}
        else:
            pass
        with db_session:
            s1 = svg2html(m1.depict())
            s2 = svg2html(m2.depict())
            reagent_img2 = s1
            product_img2 = s2
        max_path = 1
        #max_path_graph = max_path +1 # mols were not included
        paths = m1.get_effective_paths(m2, max_path)
        zero_en = paths[0].nodes[0].energy
        longest = max(len(x.nodes) for x in paths)
        nodes = {m1.id: (0, 0, reactant_color, "Complex "+str(m1.id)), m2.id: (longest * 5, (paths[0].nodes[-1].energy-zero_en)*627.51, product_color, "Complex "+str(m2.id))}
        edges = []
        for r, path in enumerate(paths):
            #nodes[path.nodes[0].id] = (1 * max_path_graph, 0,  molecule_color, True)
            for n, (x, c) in enumerate(zip(path.nodes, [0]+path.cost), start=1):
                if x.id not in nodes:
                    nodes[x.id] = (n * 5, (x.energy - zero_en)*627.51 if n % 2 else (x.energy - zero_en + c)*627.51, molecule_color if n % 2 else reaction_color, "Complex "+str(x.id) if n % 2 else "Reaction")
            #edges.append(nodes[m1.id][:2])
            for n in path.nodes:
                edges.append(nodes[n.id][:2])
            #edges.append(nodes[m2.id][:2])
            edges.append((None, None))
        for i in net_data['nodes']:
            if int(i['id']) in nodes:
                i['color'] = nodes[int(i['id'])][2]

        path_graph_data = get_figure(edges, nodes)

        return reagent_img2, product_img2, path_graph_data, net_data, struct_d3

    elif element_id == 'paths-graph' and path_graph_click:
        struct_d3 = draw(path_graph_click)
        id = path_graph_click['points'][0]['pointIndex']
        path_graph_data['data'][1]['marker']['color'][0] = reactant_color
        path_graph_data['data'][1]['marker']['color'][1] = product_color
        for n, i in enumerate(path_graph_data['data'][1]['marker']['color'][2:], start=2):
            if not n % 2:
                path_graph_data['data'][1]['marker']['color'][n] = reaction_color
            else:
                path_graph_data['data'][1]['marker']['color'][n] = molecule_color
        path_graph_data['data'][1]['marker']['color'][id] = "green"
        return reagent_img2, product_img2, path_graph_data, net_data, struct_d3

    elif element_id == 'net' and netid is not None:
        #print(net_data)
        for i in net_data['nodes']:
            if i['id'] == netid:
                i['color'] = 'red'
        return reagent_img2, product_img2, path_graph_data, net_data, struct_d3
    elif element_id == 'net' and netid is not None:
        return reagent_img2, product_img2, path_graph_data, net_data, struct_d3
    print("blanc")
    reagent_img2 = ""
    product_img2 = ""
    path_graph_data = Figure()
    net_data = {'nodes': [], 'links': []}
    struct_d3 = {'atoms': [], 'bonds': []}
    return reagent_img2, product_img2, path_graph_data, net_data, struct_d3

    #return reagent_img2, product_img2, path_graph_data, net_data, struct_d3


#@dash.callback(Output('structure', 'value'), [Input('paths-graph', 'clickData')])
def draw(click_data):
    if not click_data:
        return {'atoms': [], 'bonds': []}
    if "customdata" not in click_data['points'][0]:
        return {'atoms': [], 'bonds': []}
    _id, identifier = click_data['points'][0]['customdata']
    with db_session:
        if identifier == "MOL" or "Complex" in identifier:
            if identifier == "MOL":
                #node = Molecule.get(_id)
                pass
            if "Complex" in identifier:
                node = Complex.get(_id)
            eq = node.equilibrium_states.order_by('energy').first()
            mp = node.equilibrium_states.relationship(eq).mapping
            xyz = {mp[k]: v for k, v in eq.xyz.items()}
            s = node.structure
            order_map = {n: i for i, n in enumerate(s)}
            tmp = {'atoms': [{'elem': a.atomic_symbol, 'x': xyz[n][0], 'y': xyz[n][1], 'z': xyz[n][2]}
                             for n, a in s.atoms()],
                   'bonds': [{'atom1': order_map[n], 'atom2': order_map[m], 'maxorder': b.order}
                             for n, m, b in s.bonds()]}
        else:
            node = Reaction.get(_id)
            ts = node.transition_states.order_by('energy').first()
            mp = node.transition_states.relationship(ts).mapping
            xyz = {mp[k]: v for k, v in ts.xyz.items()}
            s = node.structure
            order_map = {n: i for i, n in enumerate(s)}
            tmp = get_3d(s, order_map, xyz)

    return tmp




__all__ = ['dash']
