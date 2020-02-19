# -*- coding: utf-8 -*-
#
#  Copyright 2020 Ramil Nugmanov <nougmanoff@protonmail.com>
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

# todo: fix header. add CLI.
import argparse
parser = argparse.ArgumentParser(description="fill DB with data")
group = parser.add_mutually_exclusive_group()
#group.add_argument("-v", "--verbose", action="store_true")
#group.add_argument("-q", "--quiet", action="store_true")
parser.add_argument('--eq_file', '-eq', type=str, help="the file with equilibrium states")
parser.add_argument('--ts_file', '-ts', type=str, help="the file with transition states")
parser.add_argument('--pt_file', '-pt', type=str, help="the file with scan pathways", default=None, required=False)
parser.add_argument('--user', '-u', default='postgres', help='admin login')
parser.add_argument('--password', '-p', required=True, help='admin pass')
parser.add_argument('--host', '-H', default='localhost', help='host name')
parser.add_argument('--port', '-P', default=54320, help='database port')
parser.add_argument('--base', '-b', default='postgres', help='database name')
args = parser.parse_args()