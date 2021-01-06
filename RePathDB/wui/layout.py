# -*- coding: utf-8 -*-
#
#  Copyright 2020 Ramil Nugmanov <nougmanoff@protonmail.com>
#  Copyright 2020 Timur Gimadiev <timur.gimadiev@gmail.com>
#  This file is part of RePathDB.
#
#  RePathDB is free software; you can redistribute it and/or modify
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
from dash_core_components import Markdown, Graph, Loading
from dash_uploader import Upload, configure_upload
import uuid
from dash_html_components import Div, H1, Hr, Img, H2
from dash_marvinjs import DashMarvinJS
from dash_table import DataTable
from mol3d_dash import Mol3dDash
from dash_network import Network


reactant_color = '#8fbff2'
product_color = '#fcca95'
molecule_color = 'blue'
reaction_color = 'red'

readme = '''
# Instructions

### RePath DB GUI
The Graphical User Interface consists of four main sections:

  * Query preparation
  *	Retrieved molecules 
  *	Retrieved complexes 
  * Reactions pathways

### Query preparation

![1.png](/assets/1.png)

Reaction query is created in a molecular structure sketcher. Both the reactant and product are required.
Once the structures are drawn, click the Upload button (circled in red) to submit the query to the database.
The search in the database is performed by substructure and similarity of reactant and product molecules.

### Retrieved molecules and retrieved complexes

![2.png](/assets/2.png)

Retrieved structures are then ranked by similarity (Tanimoto coefficient) and shown in the Molecules Table as SMILES
code (on the left). The reactants are shown in light blue, the products in light brown. Particular reactant/product pair
can be selected by clicking on the radio button on the left. For the selected pair, all complexes containing either 
reactant or product molecules are shown in the Complexes table (on the right). Selection of a pair of related Complexes
allows to analyze one or several reaction pathways connecting them. Additionally, the 2D structures of the selected 
reactant-product pairs of molecule and complexes are visualized.  

![3.png](/assets/3.png)

### Reaction pathway analysis

Reaction pathway table provides an information about up to 5 most optimal pathways including their length (the number 
of transformations along the path) and the sum of energy barriers (used as a score to rank the pathways). 

Selecting a row by clicking the radio button on the left will show the corresponding energy diagram:

![4.png](/assets/4.png)

The color code for the diagram is the following: light blue for the reactant complex, light brown for the product complex,
blue for the intermediate equilibrium states, red for transition states. Clicking any point will show
the 3D structure of the lowest energy configuration.

![5.png](/assets/5.png)

In the case that a transition state is demonstrated, it is shown as a “3D CGR”, with the breaking bonds colored orange,
and the created bonds colored green. The structure visualization window is interactive, the structure can be rotated,
 zoomed, moved, etc.
 
![6.png](/assets/6.png) 

On the bottom of the full graph of the reaction pathway network to which the selected path belongs is shown. 
The nodes are Complexes, and the edges are Reactions. The Complexes involved in the pathway selected above are colored
according to the same color scheme. Clicking on any node will show the 2D structure of the complex (top right here)
and make the node larger to indicate it was selected.
 
Ensemble of species generated in a given reaction path exploration run can be represented as a full graph in which the nodes are Complexes, 
and the edges are Reactions. The Complexes involved in previously selected pathway are colored as on the Pathway diagram.
Clicking on any node will show the 2D structure of related complex. 

![7.png](/assets/7.png) 

'''

UPLOAD_FOLDER_ROOT = "/tmp/"


def get_layout(app):
    configure_upload(app, UPLOAD_FOLDER_ROOT, upload_api="/API/dash-upload", )

    row_0 = Div([H2("Upload to Database (log files)", style={'textAlign': 'left'}),
                 Div([Upload(id="file_upload", text='Drag and Drop files here', text_completed='''Download completed\n
                                              Started parsing file: ''', cancel_button=True, max_file_size=1800,  # 1800 Mb
                             filetypes=['zip'], upload_id=uuid.uuid1(),  # Unique session id
                             ), Loading(id='file_upload-output', children=[])])])
    row_1 = Div([Div([DashMarvinJS(id='editor', marvin_url=app.get_asset_url('mjs/editor.html'), marvin_width='100%')],
                     className='col-md-6'),
                 Div([Markdown(readme)], style={"maxHeight": "400px", "overflow": "scroll"}, className='col-md-6')],
                className='row')
    row_2 = Div(
            [Div([DataTable(id='table', columns=[  # {'name': 'Reactant', 'id': 'reactant', 'color': reactant_color},
                    # {'name': 'Product', 'id': 'product', 'color': product_color},
                    {'name': 'Reactant molecule SMILES', 'id': 'reactant_structure'},
                    {'name': 'Product molecule SMILES', 'id': 'product_structure'}],
                            fixed_rows={'headers': True, 'data': 0}, row_selectable='single',
                            style_data={'whiteSpace': 'normal', 'height': 'auto'},
                            style_table={'maxHeight': '300px', 'overflowY': 'hidden', 'overflowX': 'hidden'},
                            # hidden_columns=['reactant', 'product'],
                            style_cell={'textAlign': 'left'}, style_as_list_view=True, style_cell_conditional=[
                        {'if': {'column_id': 'reactant_structure'}, 'backgroundColor': reactant_color, 'width': '47%'},
                        {'if': {'column_id': 'product_structure'}, 'backgroundColor': product_color, 'width': '47%'}]),

                  ], className='col-6'),

             Div([DataTable(id='table2', columns=[  # {'name': 'Reactant', 'id': 'reactant', 'color': reactant_color},
                     # {'name': 'Product', 'id': 'product', 'color': product_color},
                     {'name': 'Reactant complex SMILES', 'id': 'reactant_structure'},
                     {'name': 'Product complex SMILES', 'id': 'product_structure'}],
                            fixed_rows={'headers': True, 'data': 0}, row_selectable='single',
                            style_data={'whiteSpace': 'normal', 'height': 'auto'},
                            style_table={'maxHeight': '300px', 'overflowY': 'scroll', 'overflowX': 'hidden'},
                            # hidden_columns=['reactant', 'product'],
                            style_cell={'textAlign': 'left'}, style_as_list_view=True, style_cell_conditional=[
                         {'if': {'column_id': 'reactant_structure'}, 'backgroundColor': reactant_color, 'width': '47%'},
                         {'if': {'column_id': 'product_structure'}, 'backgroundColor': product_color, 'width': '47%'}]),

                  ], className='col-6')], className='row')

    row_2_2 = Div([H2("Molecules structure", style={'textAlign': 'center'}), Hr(), Div([
            Img(src='', id='reagent_img', width="50%", height="100%",
                style={'backgroundColor': reactant_color, 'maxHeight': '200px'}),
            Img(src='', id='product_img', width="50%", height="100%",
                style={'backgroundColor': product_color, 'maxHeight': '200px'})], className='row'),
                   H2("Complexes structure", style={'textAlign': 'center'}), Hr(), Div([
                    Img(src='', id='reagent_img2', width="50%", height="100%",
                        style={'backgroundColor': reactant_color, 'maxHeight': '200px'}),
                    Img(src='', id='product_img2', width="50%", height="100%",
                        style={'backgroundColor': product_color, 'maxHeight': '200px'})], className='row')])

    row_3 = Div([DataTable(id='table3', columns=[  # {'name': 'Reactant', 'id': 'reactant', 'color': reactant_color},
            {'name': 'EmpiricalFormula', 'id': 'brutto'}, {'name': 'Reactions in path', 'id': 'len'},
            {'name': 'Sum of barriers', 'id': 'energy'}], fixed_rows={'headers': True, 'data': 0},
                           row_selectable='single', style_data={'whiteSpace': 'normal', 'height': 'auto'},
                           style_table={'maxHeight': '300px', 'overflowY': 'scroll', 'overflowX': 'hidden'},
                           # hidden_columns=['reactant', 'product'],
                           style_cell={'textAlign': 'left'}, style_as_list_view=True,
                           style_cell_conditional=[{'if': {'column_id': 'brutto'}, 'width': '50%'},
                                                   {'if': {'column_id': 'len'}, 'width': '20%'},
                                                   {'if': {'column_id': 'energy'}, 'width': '20%'}]), Hr(), Div(
            [Div([Graph(id='paths-graph')], className='col-md-8'),
             Div([Mol3dDash(id='structure')], className='col-md-4')], style={'min-height': '400px'},
            className='row col-12')])
    row_4 = Div([Network(id='net', width=1000, height=1000, data={'nodes': [], 'links': []}),
                 Img(src='', id='net_img', width="30%", height="100%", style={'maxHeight': '200px'}), ],
                className='row')

    layout = Div(
            [H1("RePath DB graphical user interface", style={'textAlign': 'center'}), row_0, Hr(), row_1, Hr(), row_2,
             Hr(), row_2_2, Hr(), row_3, Hr(), row_4])
    return layout
