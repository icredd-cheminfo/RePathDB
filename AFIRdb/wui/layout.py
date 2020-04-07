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
from dash_core_components import Markdown, Graph
from dash_html_components import Div, H1, Hr, Img
from dash_marvinjs import DashMarvinJS
from dash_table import DataTable
from mol3d_dash import Mol3dDash

reactant_color = '#A6A15E'
product_color = '#D0B09E'
molecule_color = 'blue'
reaction_color = 'red'

readme = '''
# Readme
- Help will be shown here
'''


def get_layout(app):
    row_1 = Div([
        Div([
            Div([
                DashMarvinJS(id='editor', marvin_url=app.get_asset_url('mjs/editor.html'), marvin_width='100%'),
                Markdown(readme)
            ], className='col'),
        ], className='col'),
        Div([DataTable(id='table', columns=[#{'name': 'Reactant', 'id': 'reactant', 'color': reactant_color},
                                            #{'name': 'Product', 'id': 'product', 'color': product_color},
                                            {'name': 'Start molecule SMILES', 'id': 'reactant_structure'},
                                            {'name': 'Finish molecule SMILES', 'id': 'product_structure'}],
                       row_selectable='single',
                       style_data={
                           'whiteSpace': 'normal',
                           'height': 'auto'},
                       style_table={'maxHeight': '300px', 'overflowY': 'scroll','overflowX':'hidden'},
                       #hidden_columns=['reactant', 'product'],
                       style_cell={'textAlign': 'left'},
                       style_as_list_view=True,
                       style_cell_conditional=[{
                           'if': {'column_id': 'reactant_structure'},
                           'backgroundColor': reactant_color
                       },
                           {
                               'if': {'column_id': 'product_structure'},
                               'backgroundColor': product_color
                           }
                       ]),
             Div([Img(src='', id='reagent_img', width="50%", height="100%",
                           style={'backgroundColor': reactant_color, 'maxHeight': '200px'}),
                  Img(src='', id='product_img', width="50%", height="100%",
                           style={'backgroundColor': product_color, 'maxHeight': '200px'})], className='row'),
             DataTable(id='table2', columns=[  # {'name': 'Reactant', 'id': 'reactant', 'color': reactant_color},
                 # {'name': 'Product', 'id': 'product', 'color': product_color},
                 {'name': 'Start complex SMILES', 'id': 'reactant_structure'},
                 {'name': 'Finish complex SMILES', 'id': 'product_structure'}],
                       row_selectable='single',
                       style_data={
                           'whiteSpace': 'normal',
                           'height': 'auto'},
                       style_table={'maxHeight': '300px', 'overflowY': 'scroll', 'overflowX': 'hidden'},
                       # hidden_columns=['reactant', 'product'],
                       style_cell={'textAlign': 'left'},
                       style_as_list_view=True,
                       style_cell_conditional=[{
                           'if': {'column_id': 'reactant_structure'},
                           'backgroundColor': reactant_color
                       },
                           {
                               'if': {'column_id': 'product_structure'},
                               'backgroundColor': product_color
                           }
                       ]),
             Div([Img(src='', id='reagent_img2', width="50%", height="100%",
                      style={'backgroundColor': reactant_color, 'maxHeight': '200px'}),
                  Img(src='', id='product_img2', width="50%", height="100%",
                      style={'backgroundColor': product_color, 'maxHeight': '200px'})], className='row'),
                  ], className='col')
    ], className='row')

    row_2 = Div([Div([Graph(id='paths-graph')], className='col-md-8'),
                 Div([Mol3dDash(id='structure')], className='col-md-4')],  style={'min-height': '300px'},
                className='row col-md-12')

    layout = Div([H1("AFIR database visualisation", style={'textAlign': 'center'}), row_1, Hr(), row_2])
    return layout
