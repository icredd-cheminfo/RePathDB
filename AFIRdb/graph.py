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
from CGRdb import Molecule as pMolecule
from CGRtools import MoleculeContainer, ReactionContainer
from collections import namedtuple, Counter
from functools import reduce
from neomodel import (StructuredNode, StructuredRel, IntegerProperty, FloatProperty, JSONProperty, RelationshipTo,
                      RelationshipFrom, One, NodeMeta, StringProperty, DoesNotExist, UniqueProperty)
from operator import or_
from pony.orm import db_session, flush


weighted_path = namedtuple('WeightedPath', ['nodes', 'cost', 'total_cost'])


class ExtNodeMeta(NodeMeta):
    def __getitem__(cls, _id):
        o = cls(id=_id)
        o.refresh()
        return o


class Mixin:
    @classmethod
    def get(cls, _id):
        o = cls(id=_id)
        try:
            o.refresh()
        except DoesNotExist:
            return
        return o

    def __hash__(self):
        return self.id


class Barrier(StructuredRel):
    energy = FloatProperty()


class Mapping(StructuredRel):
    mapping_json = JSONProperty()

    @property
    def mapping(self):
        return {int(k): v for k, v in self.mapping_json.items()}

class M_and_B(Mapping,Barrier):
    pass

class Brutto(Mixin, StructuredNode, metaclass=ExtNodeMeta):
    """
    Unique index of systems
    """
    brutto = StringProperty(unique_index=True, required=True)
    name = StringProperty()

    complexes = RelationshipTo('Complex', 'B2C')
    reactions = RelationshipTo('Reaction', 'B2R')

    def __init__(self, structure: MoleculeContainer = None, **kwargs):
        if structure is not None:
            if kwargs:
                raise ValueError('only structure argument allowed')
            brutto = ''.join(f'{a}{n}' for a, n in
                             sorted(Counter(a.atomic_symbol for _, a in structure.atoms()).items()))
            super().__init__(id=self.get_or_create({'brutto': brutto}, lazy=True)[0].id, brutto=brutto)
        else:
            super().__init__(**kwargs)

    def __str__(self):
        if self.name:
            return f'{self.brutto} ({self.name})'
        return self.brutto


class Molecule(Mixin, StructuredNode, metaclass=ExtNodeMeta):
    """
    Mapping of CGRdb Molecule into graph
    """
    cgrdb = IntegerProperty(unique_index=True, required=True)
    complexes = RelationshipTo('Complex', 'M2C', model=Mapping)

    def __init__(self, structure: MoleculeContainer = None, **kwargs):
        if structure is not None:  # get or create Molecule from structure
            if kwargs:
                raise ValueError('only structure argument allowed')
            with db_session:
                found = pMolecule.find_structure(structure)
                if not found:
                    structure.clean2d()
                    found = pMolecule(structure)
                    flush()
                    super().__init__(cgrdb=found.id)
                    self.save()
                else:  # load existing or fix broken links
                    super().__init__(id=self.get_or_create({'cgrdb': found.id}, lazy=True)[0].id, cgrdb=found.id)
        else:
            super().__init__(**kwargs)

    def has_path(self, target: 'Molecule'):
        if target.id == self.id:
            return False
        q = f'''MATCH path = (a:Molecule{{cgrdb:{self.cgrdb}}})-[:M2C]-(n)-[:C2R|:R2C*..10]-(m)-[:M2C]-(c:Molecule{{cgrdb:{target.cgrdb}}})
WHERE id(n)<>id(m)
WITH path LIMIT 1
RETURN 1 as found'''
        print(self.cgrdb, target.cgrdb)
        return bool(self.cypher(q)[0])

    def get_effective_paths(self, target: 'Molecule', limit: int = 1):
        if not limit:
            raise ValueError('limit should be positive')
        q = f'''MATCH (:Molecule{{cgrdb:{self.cgrdb}}})-[]->(start:Complex)
MATCH (:Molecule{{cgrdb:{target.cgrdb}}})-[]->(end:Complex)
WITH start,end
CALL algo.kShortestPaths.stream(start, end, {limit}, null, {{nodeQuery:'MATCH (n) WHERE n:Complex OR n:Reaction RETURN id(n) as id',
relationshipQuery:'MATCH (n:Complex)-[a:C2R]->(r:Reaction)
RETURN id(n) as source, id(r) as target, a.energy as weight
UNION
MATCH (r:Reaction)<-[:R2C]-(n:Complex)
RETURN id(r) as source, id(n) as target, 0 as weight',graph:"cypher"}})
YIELD index, nodeIds, costs
RETURN nodeIds AS path, costs, reduce(acc = 0.0, cost in costs | acc + cost) AS total_cos'''
        paths = []
        cache = {}
        for nodes, costs, total in self.cypher(q)[0]:
            nodes = tuple(cache.get(n) or cache.setdefault(n, (Reaction if i % 2 else Complex).get(n))
                          for i, n in enumerate(nodes))
            paths.append(weighted_path(nodes, costs, total))
        return paths

    @property
    @db_session
    def structure(self):
        return pMolecule[self.cgrdb].structure

    def depict(self):
        return self.structure.depict()

    def _repr_svg_(self):
        return self.depict()

    def __str__(self):
        return str(self.structure)


class Complex(Mixin, StructuredNode, metaclass=ExtNodeMeta):
    """
    Gate object for join Molecules from CGRdb with EquilibriumState`s
    """
    signature = StringProperty(unique_index=True, required=True)  # signature of Complex
    energy = FloatProperty()
    brutto = RelationshipFrom('Brutto', 'B2C', cardinality=One)
    molecules = RelationshipFrom('Molecule', 'M2C', model=Mapping)  # mapping of Molecules in db into Complex
    equilibrium_states = RelationshipFrom('EquilibriumState', 'E2C', model=Mapping)  # mapping of ES into complex
    reactant = RelationshipTo('Reaction', 'C2R', model=M_and_B)
    product = RelationshipFrom('Reaction', 'R2C', model=M_and_B)

    def __init__(self, structure: MoleculeContainer = None, **kwargs):
        if structure is not None:
            se = structure.meta['energy']
            super().__init__(signature=str(structure), energy=se)
            try:
                self.save()
            except UniqueProperty:  # already exists
                if self.energy > se:
                    self.energy = se
                self.id = self.nodes.get(signature=str(structure), lazy=True)  # get id of existing node
                e = EquilibriumState(structure)
                if not self.equilibrium_states.is_connected(e):  # only new ES need connection from complex.
                    self.equilibrium_states.connect(e, {'mapping_json': next(structure.get_mapping(self.structure))})
            else:  # new complex. store relations into CGRdb and Brutto
                #self.energy = se
                self.brutto.connect(Brutto(structure))
                # create mapping into molecules
                for s in structure.split():
                    m = Molecule(s)
                    self.molecules.connect(m, {'mapping_json': next(m.structure.get_mapping(s))})
                # store ES as-is
                e = EquilibriumState(structure)
                self.equilibrium_states.connect(e, {'mapping_json': {n: n for n in structure}})
            self.__es__ = e
        else:
            super().__init__(**kwargs)

    def get_effective_paths(self, target: 'Complex', limit: int = 1):
        if not limit:
            raise ValueError('limit should be positive')
        q = f'''MATCH (s:Complex) WHERE id(s)={self.id} 
                MATCH (f:Complex) WHERE id(f)={target.id}
                WITH s,f
                CALL algo.kShortestPaths.stream(s, f, 1, null,
                  {{
                     nodeQuery:'MATCH (n) WHERE n:Complex OR n:Reaction RETURN id(n) as id',
                     relationshipQuery:'MATCH (n:Complex)-[a:C2R]->(r:Reaction)
                                        RETURN id(n) as source, id(r) as target, a.energy as weight
                                        UNION
                                        MATCH (r:Reaction)<-[a:R2C]-(n:Complex)
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
            nodes = tuple(cache.get(n) or cache.setdefault(n, (Reaction if i % 2 else Complex).get(n))
                          for i, n in enumerate(nodes))
            paths.append(weighted_path(nodes, costs, total))
        return paths

    @property
    @db_session
    def structure(self):
        structure = []
        for m in set(self.molecules.all()):
            s = m.structure
            for r in self.molecules.all_relationships(m):
                structure.append(s.remap(r.mapping, copy=True))
        return reduce(or_, structure)

    def depict(self):
        s = self.structure
        s.clean2d()
        return s.depict()

    def _repr_svg_(self):
        return self.depict()

    def __str__(self):
        return str(self.structure)

    __es__ = None  # ad-hoc for storing associated ES


class EquilibriumState(Mixin, StructuredNode, metaclass=ExtNodeMeta):
    xyz_json = JSONProperty()
    energy = FloatProperty()

    complex = RelationshipTo('Complex', 'E2C', cardinality=One, model=Mapping)
    transition_states = RelationshipTo('TransitionState', 'E2T', model=Barrier)

    def __init__(self, structure: MoleculeContainer = None, **kwargs):
        if structure is not None:
            xyz = structure._conformers[0]
            energy = structure.meta['energy']
            # todo: check duplicates. load existing
            super().__init__(xyz_json=xyz, energy=energy)
            self.save()
        else:
            super().__init__(**kwargs)

    @property
    def xyz(self):
        return {int(k): tuple(v) for k, v in self.xyz_json.items()}


class Disabled:
    def has_path(self, target: 'Molecule'):
        if target.id == self.id:
            return False
        q = f'''MATCH 
                shortestPath((n:Molecule{{cgrdb:{self.cgrdb}}})-[:C2R|Reaction|:R2C*..]->(m:Molecule{{cgrdb:{target.cgrdb}}}))
                RETURN 1 AS found'''
        return bool(self.cypher(q)[0])

    def get_effective_paths(self, target: 'Molecule', limit: int = 1):
        if not limit:
            raise ValueError('limit should be positive')
        q = f'''MATCH (s:Molecule{{cgrdb:{self.cgrdb}}}), (f:Molecule{{cgrdb:{target.cgrdb}}})
                CALL algo.kShortestPaths.stream(s, f, {limit}, null,
                  {{
                     nodeQuery:'MATCH (n) WHERE n:Molecule OR n:Reaction RETURN id(n) as id',
                     relationshipQuery:'MATCH (n:Molecule)-[:C2R]->(r:Reaction)
                                        RETURN id(n) as source, id(r) as target, r.energy as weight
                                        UNION
                                        MATCH (r:Reaction)-[:R2C]->(n:Molecule)
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
            nodes = tuple(cache.get(n) or cache.setdefault(n, (Reaction if i % 2 else Complex).get(n))
                          for i, n in enumerate(nodes))
            paths.append(weighted_path(nodes, costs, total))
        return paths


class Reaction(Mixin, StructuredNode, metaclass=ExtNodeMeta):
    signature = StringProperty(unique_index=True, required=True)  # signature of ES2ES CGR
    energy = FloatProperty()
    brutto = RelationshipFrom('Brutto', 'B2R', cardinality=One)
    transition_states = RelationshipFrom('TransitionState', 'T2R', model=Mapping)
    reactant = RelationshipFrom('Complex', 'C2R', cardinality=One, model=M_and_B)
    product = RelationshipFrom('Complex', 'R2C', cardinality=One, model=M_and_B)

    def __init__(self, structure: ReactionContainer = None, **kwargs):
        """
        :param structure: ReactionContainer. In reactants and products contain ES`s. In reagents contains TS.
            ES`s and TS contains metadata key: energy with float value.
        """
        if structure is not None:
            r = structure.reactants[0]
            p = structure.products[0]
            t = structure.reagents[0]
            te = t.meta['energy']

            cgr = r ^ p
            super().__init__(signature=str(cgr), energy=te)
            try:
                self.save()
            except UniqueProperty:  # reaction already exists
                self.id = self.nodes.get(signature=str(cgr), lazy=True)  # get id of existing node
                ts = TransitionState(t)
                if self.energy > te:
                    self.energy = te
                rc = Complex(r)
                pc = Complex(p)
                if self.reactant.relationship(rc).energy > te - rc.energy:
                    self.reactant.relationship(rc).energy = te - rc.energy
                if self.product.relationship(pc).energy > te - pc.energy:
                    self.product.relationship(pc).energy = te - pc.energy
                if not self.transition_states.is_connected(ts):  # skip already connected TS
                    self.transition_states.connect(ts, {'mapping_json': next(cgr.get_mapping(self.structure))})
                    # connect TS to ES`s
                    re = Complex(r).__es__
                    pe = Complex(p).__es__
                    ts.equilibrium_states.connect(re, {'energy': te - re.energy})
                    ts.equilibrium_states.connect(pe, {'energy': te - pe.energy})
            else:  # new reaction
                # store relation to Brutto
                #self.energy = te
                self.brutto.connect(Brutto(t))
                # connect reactant and product complexes. todo: possible optimization of mapping
                rc = Complex(r)
                pc = Complex(p)
                self.reactant.connect(rc, {'mapping_json': next(rc.structure.get_mapping(r)), 'energy': te-rc.energy})
                self.product.connect(pc, {'mapping_json': next(pc.structure.get_mapping(p)), 'energy': te-pc.energy})

                # connect TS to R
                ts = TransitionState(t)
                self.transition_states.connect(ts, {'mapping_json': {n: n for n in t}})
                # connect TS to ES`s
                re = rc.__es__
                pe = pc.__es__
                ts.equilibrium_states.connect(re, {'energy': te - re.energy})
                ts.equilibrium_states.connect(pe, {'energy': te - pe.energy})
        else:
            super().__init__(**kwargs)

    @property
    @db_session
    def structure(self):
        r = self.reactant.single()
        p = self.product.single()
        r = r.structure.remap(self.reactant.relationship(r).mapping, copy=True)
        p = p.structure.remap(self.product.relationship(p).mapping, copy=True)
        return r ^ p

    def depict(self):
        s = self.structure
        s.clean2d()
        return s.depict()

    def _repr_svg_(self):
        return self.depict()

    def __str__(self):
        return str(self.structure)


class TransitionState(Mixin, StructuredNode, metaclass=ExtNodeMeta):
    xyz_json = JSONProperty()
    energy = FloatProperty()

    reaction = RelationshipTo('Reaction', 'T2R', cardinality=One, model=Mapping)
    equilibrium_states = RelationshipFrom('EquilibriumState', 'E2T', model=Barrier)

    def __init__(self, structure: MoleculeContainer = None, **kwargs):
        if structure is not None:
            xyz = structure._conformers[0]
            energy = structure.meta['energy']
            # todo: check duplicates. load existing
            super().__init__(xyz_json=xyz, energy=energy)
            self.save()
        else:
            super().__init__(**kwargs)

    @property
    def xyz(self):
        return {int(k): tuple(v) for k, v in self.xyz_json.items()}

__all__ = ['Molecule', 'Reaction', 'EquilibriumState', 'TransitionState', 'Barrier', 'Mapping', 'Complex', 'Brutto']
