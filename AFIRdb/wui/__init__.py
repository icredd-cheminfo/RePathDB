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
from dash import Dash
from os import getenv
from .plugins import external_scripts, external_stylesheets
from .layout import get_layout


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
