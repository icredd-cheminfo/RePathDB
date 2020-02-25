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


readme = '''
# Hey there
    - My mighty helpfull advises should be here to navigate noobies in darkspace of visualisation
    - ***star***
'''


def get_layout(app):
    row_1 = Div([
                Div([
                    Div([
                        DashMarvinJS(id='editor', marvin_url=app.get_asset_url('mjs/editor.html'), marvin_width='100%'),
                        Markdown(readme)
                        ], className='col'),
                    ], className='col-md-6'),
                Div([DataTable(id='table', columns=[{'name': 'Reactant', 'id': 'reactant'},
                                                    {'name': 'Product', 'id': 'product'},
                                                    {'name': 'Reactant SMILES', 'id': 'reactant_structure'},
                                                    {'name': 'Product SMILES', 'id': 'product_structure'}], row_selectable='single',
                               style_table={'maxHeight': '300px', 'overflowY': 'scroll'}), Div([Img(src='', id='reagent_img'),
                                                                                                Img(src='', id='product_img')])],
                    className='col-md-6')
                ], className='row col-md-12')

    row_2 = Div([Div([Graph(id='paths-graph')], className='col-md-8'),
                 Div([], id='structure', className='col-md-4')], className='row col-md-12')

    layout = Div([H1("AFIR database visualisation",  style={'textAlign': 'center'}), row_1, Hr(), row_2])
    return layout
