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
from base64 import encodebytes
from CGRdb import Molecule as pMolecule, Reaction as pReaction
from CGRtools import MoleculeContainer
from collections import namedtuple
from json import dumps
from neomodel import (StructuredNode, StructuredRel, IntegerProperty, FloatProperty, JSONProperty, RelationshipTo,
                      RelationshipFrom, One, BooleanProperty)
from pony.orm import db_session


weighted_path = namedtuple('WeightedPath', ['nodes', 'cost', 'total_cost'])
color_map = ['rgb(0,104,55)', 'rgb(26,152,80)', 'rgb(102,189,99)', 'rgb(166,217,106)', 'rgb(217,239,139)',
             'rgb(254,224,139)']
MoleculeContainer._render_config['mapping'] = False


class Barrier(StructuredRel):
    energy = FloatProperty()


class Gate(StructuredRel):
    mapping = JSONProperty()


class GetMethod:
    @classmethod
    def get(cls, _id):
        o = cls(id=_id)
        o.refresh()
        return o


class Molecule(StructuredNode, GetMethod):
    cgrdb = IntegerProperty(index=True)

    equilibrium_states = RelationshipTo('EquilibriumState', 'M2E', model=Gate)
    reactant = RelationshipTo('Reaction', 'M2R')
    product = RelationshipFrom('Reaction', 'R2M')

    @property
    @db_session
    def structure(self):
        return pMolecule[self.cgrdb].structure

    def depict(self):
        return 'data:image/svg+xml;base64,' + encodebytes(self.structure.depict().encode()).decode().replace('\n', '')

    def get_effective_paths(self, target: 'Molecule', limit: int = 1):
        if not limit:
            raise ValueError('limit should be positive')
        q = f'''MATCH (s:Molecule{{cgrdb:{self.cgrdb}}}), (f:Molecule{{cgrdb:{target.cgrdb}}})
                CALL algo.kShortestPaths.stream(s, f, {limit}, null,
                  {{
                     nodeQuery:'MATCH (n) WHERE n:Molecule OR n:Reaction RETURN id(n) as id',
                     relationshipQuery:'MATCH (n:Molecule)-[:M2R]->(r:Reaction)
                                        RETURN id(n) as source, id(r) as target, r.energy as weight
                                        UNION
                                        MATCH (r:Reaction)-[:R2M]->(n:Molecule)
                                        RETURN id(r) as source, id(n) as target, 0 as weight',
                     direction:'OUT',
                     graph:'cypher'
                   }}
                 )
                YIELD index, nodeIds, costs
                RETURN nodeIds AS path, costs, reduce(acc = 0.0, cost in costs | acc + cost) AS total_cost'''
        paths = []
        cache = {}
        for nodes, costs, total in self.cypher(q)[0]:
            nodes = tuple(cache.get(n) or cache.setdefault(n, (Reaction if i % 2 else Molecule).get(n))
                          for i, n in enumerate(nodes))
            paths.append(weighted_path(nodes, costs, total))
        return paths

    def get_effective_paths_sigma_graph(self, *args, **kwargs):
        nodes = []
        edges = []
        data = {'nodes': nodes, 'edges': edges}

        paths = self.get_effective_paths(*args, **kwargs)
        longest = max(len(x) for x, *_ in paths) - 1
        start = paths[0].nodes[0]
        target = paths[0].nodes[-1]
        nodes.append({'id': str(target.id), 'label': target.labels()[0],
                      'x': longest * 5, 'y': 0, 'size': 1, 'color': 'rgb(178,223,138)',
                      'structure': target.depict()})
        nodes.append({'id': str(start.id), 'label': start.labels()[0],
                      'x': 0, 'y': 0, 'size': 1, 'color': 'rgb(178,223,138)',
                      'structure': start.depict()})
        seen = {target.id, start.id}
        for r, (mol_rxn, costs, total) in enumerate(paths):
            for n, (x, c) in enumerate(zip(mol_rxn[1:-1], costs), start=1):
                if x.id not in seen:
                    nodes.append({'id': str(x.id),
                                  'label': f'{x.labels()[0]} ({c * 627.51:.1f})' if n % 2 else x.labels()[0],
                                  'x': n * 5, 'y': r * 3, 'size': 1,
                                  'color': 'rgb(253,191,111)' if n % 2 else 'rgb(178,223,138)',
                                  'structure': x.depict()})
                    seen.add(x.id)

            for n, m in zip(mol_rxn, mol_rxn[1:]):
                try:
                    color = color_map[r]
                except IndexError:
                    color = color_map[-1]

                edges.append({'id': f'{r}-{n.id}-{m.id}', 'source': str(n.id), 'target': str(m.id),
                              'count': r * 5, 'color': color})
        return dumps(data)


class Reaction(StructuredNode, GetMethod):
    cgrdb = IntegerProperty(index=True)

    transition_states = RelationshipTo('TransitionState', 'R2T', model=Gate)
    reactant = RelationshipFrom('Molecule', 'M2R', cardinality=One)
    product = RelationshipTo('Molecule', 'R2M', cardinality=One)

    @property
    @db_session
    def structure(self):
        return pReaction[self.cgrdb].structure

    @property
    def cgr(self):
        return ~self.structure

    def depict(self):
        s = self.cgr
        s.clean2d()
        return 'data:image/svg+xml;base64,' + encodebytes(s.depict().encode()).decode().replace('\n', '')


class EquilibriumState(StructuredNode, GetMethod):
    xyz = JSONProperty()
    energy = FloatProperty()

    molecule = RelationshipFrom('Molecule', 'M2E', cardinality=One, model=Gate)
    transition_states = RelationshipTo('TransitionState', 'E2T', model=Barrier)


class TransitionState(StructuredNode, GetMethod):
    xyz = JSONProperty()
    energy = FloatProperty()
    true_ts = BooleanProperty()

    reaction = RelationshipFrom('Reaction', 'R2T', cardinality=One, model=Gate)
    equilibrium_states = RelationshipFrom('EquilibriumState', 'E2T', model=Barrier)


__all__ = ['Molecule', 'Reaction', 'EquilibriumState', 'TransitionState', 'Barrier', 'Gate']
