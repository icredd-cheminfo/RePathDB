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
from CGRdb import Molecule as pMolecule, Reaction as pReaction
from collections import namedtuple
from neomodel import (StructuredNode, StructuredRel, IntegerProperty, FloatProperty, JSONProperty, RelationshipTo,
                      RelationshipFrom, One, BooleanProperty)
from pony.orm import db_session


weighted_path = namedtuple('WeightedPath', ['nodes', 'cost', 'total_cost'])


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
        return self.structure.depict()

    def has_path(self, target: 'Molecule'):
        if target.id == self.id:
            return False
        q = f'''MATCH 
                shortestPath((n:Molecule{{cgrdb:{self.cgrdb}}})-[:M2R|Reaction|:R2M*..]->(m:Molecule{{cgrdb:{target.cgrdb}}}))
                RETURN 1 AS found'''
        return bool(self.cypher(q)[0])

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


class Reaction(StructuredNode, GetMethod):
    cgrdb = IntegerProperty(index=True)
    energy = FloatProperty()

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
        return s.depict()


class EquilibriumState(StructuredNode, GetMethod):
    xyz = JSONProperty()
    energy = FloatProperty()

    molecule = RelationshipFrom('Molecule', 'M2E', cardinality=One, model=Gate)
    transition_states = RelationshipTo('TransitionState', 'E2T', model=Barrier)


class TransitionState(StructuredNode, GetMethod):
    xyz = JSONProperty()
    energy = FloatProperty()
    true_ts = BooleanProperty()

    reaction = RelationshipFrom('Reaction', 'R2T', model=Gate)
    equilibrium_states = RelationshipFrom('EquilibriumState', 'E2T', model=Barrier)


__all__ = ['Molecule', 'Reaction', 'EquilibriumState', 'TransitionState', 'Barrier', 'Gate']
