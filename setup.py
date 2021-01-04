#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  Copyright 2020, 2021 Ramil Nugmanov <nougmanoff@protonmail.com>
#  Copyright 2020, 2021 Timur Gimadiev <timur.gimadiev@gmail.com>
#  This file is part of RePathDB.
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
from pathlib import Path
from setuptools import setup, find_packages


version = '1.0.2'


setup(
    name='RePathDB',
    version=version,
    packages=find_packages(),
    url='https://github.com/icredd-cheminfo/RePathDB',
    license='LGPLv3',
    author='Dr. Timur Gimadiev',
    author_email='timur.gimadiev@gmail.com',
    python_requires='>=3.6.0',
    install_requires=['cgrtools[mrv,clean2djit]',
                      'CGRdb @ git+https://github.com/stsouko/CGRdb.git@4.0#egg=CGRdb',
                      'neomodel>=3.3.2', 'dash', 'dash-marvinjs', 'mol3d-dash', 'plotly', 'dash-network',
                      'dash-uploader'],
    long_description=(Path(__file__).parent / 'README.md').read_text(),
    classifiers=['Environment :: Plugins',
                 'Intended Audience :: Science/Research',
                 'Intended Audience :: Developers',
                 'Topic :: Scientific/Engineering :: Chemistry',
                 'Topic :: Software Development :: Libraries :: Python Modules',
                 'License :: OSI Approved :: GNU Lesser General Public License v3 or later (LGPLv3+)',
                 'Operating System :: OS Independent',
                 'Programming Language :: Python',
                 'Programming Language :: Python :: 3',
                 'Programming Language :: Python :: 3.7',
                 ]
)
