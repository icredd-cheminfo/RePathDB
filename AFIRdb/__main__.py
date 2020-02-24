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
from argparse import ArgumentParser, FileType, ArgumentDefaultsHelpFormatter
from CGRdb import load_schema
from neomodel import config
from urllib.parse import urlparse
from .populate import load_data
from .wui import dash


def populate_core(args):
    if not args.ts_file and not args.pt_file:
        print('At least ts_file or pt_file required')
    else:
        load_data(args.eq_file, args.ts_file, args.pt_file)


def web_core(args):
    ds = args.listening
    dash.run_server(port=ds.port, host=ds.hostname, debug=args.debug)


parser = ArgumentParser(description="fill DB with data", formatter_class=ArgumentDefaultsHelpFormatter)
parser.add_argument('--postgres', '-pg', type=urlparse, required=True,
                    help='postgres connection URL [//user:pass@host:port/schema]')
parser.add_argument('--neo4j', '-nj', type=str, required=True, help='neo4j connection URL')

subparsers = parser.add_subparsers(title='subcommands', description='available utilities')

populate = subparsers.add_parser('populate', help='load data into DB')
populate.add_argument('--eq_file', '-eq', type=FileType(), required=True, help='the file with equilibrium states')
populate.add_argument('--ts_file', '-ts', type=FileType(), help='the file with transition states')
populate.add_argument('--pt_file', '-pt', type=FileType(), help='the file with scan pathways')
populate.set_defaults(func=populate_core)

web = subparsers.add_parser('wui', help='run WEB UI', formatter_class=ArgumentDefaultsHelpFormatter)
web.add_argument('--listening', '-ls', type=urlparse,
                 help='listening host and port [//host:port]', default='//localhost:5000')
web.add_argument('--debug', action='store_true')
web.set_defaults(func=web_core)

parsed = parser.parse_args()
if 'func' in parsed:
    # setup connections
    pg = parsed.postgres
    load_schema(pg.path[1:], password=pg.password, port=pg.port, host=pg.hostname, user=pg.username)
    config.DATABASE_URL = parsed.neo4j
    # run utility
    parsed.func(parsed)
else:
    parser.print_help()
