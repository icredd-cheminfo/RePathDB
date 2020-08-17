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
from base64 import encodebytes,b64encode
from CGRdb import Molecule as pMolecule
from CGRtools import MoleculeContainer, MRVRead
from dash import Dash, callback_context
from dash.dependencies import Input, Output, State
from dash_html_components import Div
from ..graph import Molecule, Complex
from itertools import product
from io import BytesIO
from .layout import get_layout, reactant_color, product_color, reaction_color, molecule_color, UPLOAD_FOLDER_ROOT
from os import getenv, remove
from pony.orm import db_session
from .plugins import external_scripts, external_stylesheets
from plotly.graph_objects import Figure
from pathlib import Path
from ..populate import load_one_file
from .utilities import get_figure, get_3d, draw, get_mrv, cleanDB

from flask import make_response

import zipfile
from collections import Counter

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
        mrv = get_mrv(s)
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


@dash.callback([Output('reagent_img', 'src'), Output('product_img', 'src'), Output('table2', 'data'),
                Output('table2', 'selected_rows')],
               [Input('table', 'selected_rows')], [State('table', 'data')])
def graph(row_id, table):
    if not row_id:
        table = [{'reactant': 'No results', 'product': 'No results', 'reactant_structure': 'No results',
                  'product_structure': 'No results'}]
        return '', '', table, []

    row = table[row_id[0]]
    m1 = Molecule.get(row['reactant'])
    m2 = Molecule.get(row['product'])
    with db_session:
        s1 = svg2html(m1.depict())
        s2 = svg2html(m2.depict())
    max_path = 10
    # max_path_graph = max_path +1 # mols were not included
    paths = m1.get_effective_paths(m2, max_path)
    pairs = []
    for r, path in enumerate(paths):
        # print(path.nodes[0])
        # a = Complex.nodes.get(path.nodes[0])
        # b = Complex.nodes.get(path.nodes[-1])
        pairs.append({'reactant': path.nodes[0].id, 'product': path.nodes[-1].id,
                      'reactant_structure': path.nodes[0].signature, 'product_structure': path.nodes[-1].signature})
    #print(pairs)
    return s1, s2, pairs, []


@dash.callback([Output('reagent_img2', 'src'), Output('product_img2', 'src'), Output('paths-graph', 'figure'),
                Output('net', 'data'), Output('structure', 'value'), Output('net_img', 'src'),
                Output('table3', 'data')],
               [Input('table2', 'selected_rows'), Input('paths-graph', 'clickData'), Input('net', 'selectedId'),
                Input('table3', 'selected_rows')],
               [State('table2', 'data'), State('paths-graph', 'figure'), State('reagent_img2', 'src'),
                State('product_img2', 'src'), State('net', 'data'), State('structure', 'value'),
                State('net_img', 'src'),
                State('table3', 'data')])
def graph(row_id2_inp, path_graph_click, netid, table3_row, table2, path_graph_data, reagent_img2, product_img2,
          net_data,
          struct_d3, net_img, table3_data):
    ctx = callback_context
    element_id = ctx.triggered[0]['prop_id'].split('.')[0]
    print(ctx.triggered[0])
    if element_id == 'table3' and not table3_row:
        return reagent_img2, product_img2, path_graph_data, net_data, struct_d3, net_img, table3_data

    elif element_id == 'table2' and row_id2_inp:
        row = table2[row_id2_inp[0]]
        m1 = Complex.get(row['reactant'])
        m2 = Complex.get(row['product'])
        b1 = m1.brutto.all()[0]
        b2 = m2.brutto.all()[0]
        if b1 == b2:
            graph_nodes = [{'id': str(x.id), 'color': "grey"} for x in b1.complexes.all()]
            graph_links = [{'source': r.reactant.all()[0].id, 'target': r.product.all()[0].id, 'color': "green"} for r
                           in b1.reactions.all()]
            net_data = {'nodes': graph_nodes, 'links': graph_links}
        else:
            pass
        with db_session:
            s1 = svg2html(m1.depict())
            s2 = svg2html(m2.depict())
            reagent_img2 = s1
            product_img2 = s2
        max_path = 10
        # max_path_graph = max_path +1 # mols were not included
        paths = m1.get_effective_paths(m2, max_path)
        # print(paths)
        table3_data = []
        longest = max(len(path.nodes) for path in paths)
        for path in sorted(paths, key=lambda x: (((len(x.nodes) - 1) / 2), x.total_cost)):  # дальше тихий ужас. но пока лень переписывать
            #paths = [paths]
            zero_en = path.nodes[0].energy
            #longest = max(len(path.nodes))# for x in paths)
            nodes = {m1.id: (0, 0, reactant_color, "Complex " + str(m1.id)), m2.id: (
                longest * 5, (path.nodes[-1].energy - zero_en) * 627.51, product_color, "Complex " + str(m2.id))}
            edges = []
            print(path)
            d = {}
            d["brutto"] = str(b1)
            d["energy"] = round(path.total_cost * 627.51, 2)
            # nodes[path.nodes[0].id] = (1 * max_path_graph, 0,  molecule_color, True)
            for n, (x, c) in enumerate(zip(path.nodes, path.cost), start=1):
                if x.id not in nodes:
                    nodes[x.id] = (
                    n * 5, (x.energy - zero_en) * 627.51 if n % 2 else (x.energy - zero_en + c) * 627.51,
                    molecule_color if n % 2 else reaction_color,
                    "Complex " + str(x.id) if n % 2 else "Reaction")
            # edges.append(nodes[m1.id][:2])
            d["len"] = (len(nodes) - 1) / 2
            for n in path.nodes:
                edges.append(nodes[n.id][:2])
            # edges.append(nodes[m2.id][:2])
            edges.append((None, None))
            d["nodes"] = nodes
            d["path_graph_data"] = get_figure(edges, nodes)
            table3_data.append(d)
        # print(table3_data)
        return reagent_img2, product_img2, path_graph_data, net_data, struct_d3, net_img, table3_data

    elif element_id == 'table3' and table3_row:
        row = table3_data[table3_row[0]]
        nodes = row["nodes"]
        print(nodes)
        for i in net_data['nodes']:
            i['radius'] = 10
            if i['id'] in nodes:
                i['color'] = nodes[i['id']][2]
        path_graph_data = row["path_graph_data"]
        return reagent_img2, product_img2, path_graph_data, net_data, struct_d3, net_img, table3_data

    elif element_id == 'paths-graph' and path_graph_click:
        # print(path_graph_data['data'][1]['marker'])
        # print(path_graph_click)
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
        id_c = path_graph_click['points'][0]['customdata'][0]
        net_img = ""
        for i in net_data['nodes']:
            i['radius'] = 10
            if i['id'] == str(id_c):
                i['radius'] = 20
                with db_session:
                    m = Complex.get(int(id_c))
                    if m is not None:
                        net_img = svg2html(m.depict())

        return reagent_img2, product_img2, path_graph_data, net_data, struct_d3, net_img, table3_data

    elif element_id == 'net' and netid is not None:
        # print(net_data)
        for i in net_data['nodes']:
            i['radius'] = 10
            if i['id'] == netid:
                i['radius'] = 20
                with db_session:
                    m = Complex.get(int(netid))
                    net_img = svg2html(m.depict())
        return reagent_img2, product_img2, path_graph_data, net_data, struct_d3, net_img, table3_data

    elif element_id == 'net' and netid is None:
        return reagent_img2, product_img2, path_graph_data, net_data, struct_d3, net_img, table3_data

    else:
        print("blanc")
        reagent_img2 = ""
        product_img2 = ""
        path_graph_data = Figure()
        net_data = {'nodes': [], 'links': []}
        struct_d3 = {'atoms': [], 'bonds': []}
        net_img = ""
        table3_data = [{'brutto': 'No results', 'len': 'No results', 'energy': 'No results'}]
        return reagent_img2, product_img2, path_graph_data, net_data, struct_d3, net_img, table3_data


@dash.callback(Output('file_upload-output', 'children'),
               [Input('file_upload', 'isCompleted')],
               [State('file_upload', 'fileNames'),
                State('file_upload', 'upload_id')], )
def get_files(iscompleted, filenames, upload_id):
    ctx = callback_context
    element_id = ctx.triggered[0]['prop_id'].split('.')[0]
    print(element_id)
    if not iscompleted:
        return

    if filenames is not None:
        if upload_id:
            root_folder = Path(UPLOAD_FOLDER_ROOT) / upload_id
        else:
            root_folder = Path(UPLOAD_FOLDER_ROOT)
        counter = Counter()
        for filename in filenames:
            file = root_folder / filename
            archive = zipfile.ZipFile(file, 'r')
            for one in archive.namelist()[1:]:
                print(one)
                with archive.open(one) as file_open:
                    counter[load_one_file(file_open)] += 1
            remove(file)
            print("{} removed".format(file))
        return Div([
            '{} log files were processed and added to database, {} files were not processed due to errors,'
            ' not log files are omitted and were not taken into account'.format(counter["good"], counter["bad"])
        ])

    return Div("No Files Uploaded Yet!")


@dash.server.route('/pictures/<name>')
def get_picture(name):
    if name is not None:
        encoded_image = b64encode(
            open("/usr/local/lib/python3.6/dist-packages/AFIRdb/wui" + dash.get_asset_url(name), 'rb').read())
        # resp = Img(src='data:image/png;base64,{}'.format(encoded_image.decode()))
        resp = make_response('data:image/png;base64,{}'.format(encoded_image))
        resp.headers['Content-Type'] = 'image/png'
        return resp


__all__ = ['dash']
