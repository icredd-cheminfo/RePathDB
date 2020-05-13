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
from dash_core_components import Markdown, Graph, RadioItems
from dash_html_components import Div, H1, Hr, Img, Br,H2
from dash_marvinjs import DashMarvinJS
from dash_table import DataTable
from mol3d_dash import Mol3dDash
from dash_network import Network

reactant_color = '#93e3ed'
product_color = '#f77ea5'
molecule_color = 'blue'
reaction_color = 'red'

readme = '''
# Instructions
- Help will be shown here
'''


def get_layout(app):
    row_1 = Div([
                Div([
                    DashMarvinJS(id='editor', marvin_url=app.get_asset_url('mjs/editor.html'), marvin_width='100%')
            ], className='col-md-6'),
                Div([
                    Markdown(readme)
                ], className='col-md-6')
            ], className='row')
    row_2 =Div([
        Div([DataTable(id='table', columns=[#{'name': 'Reactant', 'id': 'reactant', 'color': reactant_color},
                                            #{'name': 'Product', 'id': 'product', 'color': product_color},
                                            {'name': 'Reactant molecule SMILES', 'id': 'reactant_structure'},
                                            {'name': 'Product molecule SMILES', 'id': 'product_structure'}],
                       fixed_rows={'headers': True, 'data': 0},
                       row_selectable='single',
                       style_data={
                           'whiteSpace': 'normal',
                           'height': 'auto'},
                       style_table={'maxHeight': '300px', 'overflowY': 'hidden','overflowX':'hidden'},
                       #hidden_columns=['reactant', 'product'],
                       style_cell={'textAlign': 'left'},
                       style_as_list_view=True,
                       style_cell_conditional=[{
                           'if': {'column_id': 'reactant_structure'},
                           'backgroundColor': reactant_color,
                           'width': '47%'
                       },
                           {
                           'if': {'column_id': 'product_structure'},
                           'backgroundColor': product_color,
                           'width': '47%'
                           }
                       ]),

             ], className='col-6'),

        Div([DataTable(id='table2', columns=[  # {'name': 'Reactant', 'id': 'reactant', 'color': reactant_color},
                                                 # {'name': 'Product', 'id': 'product', 'color': product_color},
                                                 {'name': 'Reactant complex SMILES', 'id': 'reactant_structure'},
                                                 {'name': 'Product complex SMILES', 'id': 'product_structure'}],
                       fixed_rows={'headers': True, 'data': 0},
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
                           'backgroundColor': reactant_color,
                           'width': '47%'
                       },
                           {
                           'if': {'column_id': 'product_structure'},
                           'backgroundColor': product_color,
                           'width': '47%'
                           }
                       ]),

                  ], className='col-6')
             ], className='row')

    row_2_2 = Div([
        H2("Molecules structure", style={'textAlign': 'center'}),
        Hr(),
        Div([
            Img(src='', id='reagent_img', width="50%", height="100%",
                           style={'backgroundColor': reactant_color, 'maxHeight': '200px'}),
            Img(src='', id='product_img', width="50%", height="100%",
                           style={'backgroundColor': product_color, 'maxHeight': '200px'})
                  ], className='row'),
        H2("Complexes structure", style={'textAlign': 'center'}),
        Hr(),
        Div([
            Img(src='', id='reagent_img2', width="50%", height="100%",
                      style={'backgroundColor': reactant_color, 'maxHeight': '200px'}),
            Img(src='', id='product_img2', width="50%", height="100%",
                      style={'backgroundColor': product_color, 'maxHeight': '200px'})], className='row')
    ])

    row_3 = Div([RadioItems(id='radio',
                               options=[
                                   {'label': 'Best', 'value': '1'},
                                   {'label': 'Second', 'value': '2'},
                                   {'label': 'Third', 'value': '3'},
                                   {'label': 'Fourth', 'value': '4'},
                                   {'label': 'Fifth', 'value': '5'}
                               ],
                               value='1',
                               labelStyle={'display': 'inline-block', }
                               ),
                Br(),
                Div([Div([Graph(id='paths-graph')], className='col-md-8'),
                    Div([Mol3dDash(id='structure')], className='col-md-4')],  style={'min-height': '400px'},
                            className='row col-12')
            ])
    row_4 = Div([Network(
                    id='net',
                    width=1000,
                    height=1000,
                    data={'nodes': [],
                          'links': []
                    }),
                Img(src='', id='net_img', width="30%", height="100%",
                        style={'maxHeight': '200px'}),
    ], className='row')

    layout = Div([H1("AFIR database visualisation", style={'textAlign': 'center'}),
                  row_1, Hr(), row_2, Hr(), row_2_2, Hr(), row_3, Hr(), row_4])
    return layout
