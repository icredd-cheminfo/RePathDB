# -*- coding: utf-8 -*-
#
#  Copyright 2020, 2021 Ramil Nugmanov <nougmanoff@protonmail.com>
#  Copyright 2020, 2021 Timur Gimadiev <timur.gimadiev@gmail.com>
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
from CGRdb import Molecule as pMolecule
from CGRtools import MoleculeContainer, ReactionContainer
from CGRtools.algorithms.x3dom import JupyterWidget
from collections import namedtuple, Counter
from functools import reduce
from neomodel import (StructuredNode, StructuredRel, IntegerProperty, FloatProperty, JSONProperty, RelationshipTo,
                      RelationshipFrom, One, NodeMeta, StringProperty, DoesNotExist, UniqueProperty)
from operator import or_
from pony.orm import db_session, flush
from itertools import count
from itertools import islice
from heapq import heappush, heappop


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


class M_and_B(Mapping, Barrier):
    pass


class Brutto(Mixin, StructuredNode, metaclass=ExtNodeMeta):
    """
    Node type for the Neo4j
    Unique index of systems defined by empirical formula
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
    Node type for NEO4j
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

    def search_path(self, target: 'Molecule', max_len=10):
        seen = set(self.complexes.all())
        final_compl = set(target.complexes.all())
        cur_compl = seen - final_compl
        final_compl -= seen
        if not final_compl:
            return
        queue = []
        n = count()
        for x in cur_compl:
            heappush(queue, (1, 0, next(n), [(x, 0)]))
        old_len = 1
        new_seen = set()
        while queue:
            level, prev_barrier, _, init_path = heappop(queue)
            cur = init_path[-1][0]
            if len(init_path) != old_len:
                seen.update(new_seen)
                old_len = len(init_path)
            cur_len = len(init_path) + 1 < max_len
            for i, r in enumerate(cur.reactant.all()):
                barrier = (r.energy - cur.energy)  # * 627.51 have not yet decided which units
                # barrier = barrier if barrier > prev_barrier else prev_barrier
                prod = r.product.all()[0]
                if prod in final_compl:
                    path = init_path.copy()
                    path.append((r, barrier))
                    path.append((prod, barrier))
                    yield path
                elif cur_len and prod not in seen:
                    new_seen.add(prod)
                    path = init_path.copy()
                    path.append((r, barrier))
                    path.append((prod, barrier))
                    heappush(queue, (len(path), barrier, next(n), path))

    def has_path(self, target: 'Molecule'):
        if target.id == self.id:
            return False
        return bool(next(self.search_path(target), False))

    def get_effective_paths(self, target: 'Molecule', limit: int = 10):
        if limit <= 0:
            raise ValueError('limit should be positive')

        paths = []
        for path in islice(self.search_path(target, limit), 30):
            nodes = []
            costs = []
            total = 0
            for i, (node, barrier) in enumerate(path, start=1):
                nodes.append(node)
                costs.append(barrier) if i % 2 == 0 else costs.append(0)
                total += costs[-1]
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
            # load ES first for validation
            e = EquilibriumState(structure)

            super().__init__(signature=str(structure), energy=se)
            try:
                self.save()
            except UniqueProperty:  # already exists
                self.id = self.nodes.get(signature=str(structure), lazy=True)  # get id of existing node
                self.refresh()

                # new lowest ES found
                if self.energy > se:  # this can break existing reaction barriers values!
                    # check ES is new
                    if self.equilibrium_states.is_connected(e):
                        raise ValueError('same EquilibriumState with different energy exists')
                    self.energy = se
                    self.save()
                    self.equilibrium_states.connect(e, {'mapping_json': next(structure.get_mapping(self.structure))})
                elif not self.equilibrium_states.is_connected(e):  # only new ES need connection from complex.
                    self.equilibrium_states.connect(e, {'mapping_json': next(structure.get_mapping(self.structure))})
            else:  # new complex. store relations into CGRdb and Brutto
                self.brutto.connect(Brutto(structure))
                # create mapping into molecules
                for s in structure.split():
                    m = Molecule(s)
                    self.molecules.connect(m, {'mapping_json': next(m.structure.get_mapping(s))})
                # store ES as-is
                self.equilibrium_states.connect(e, {'mapping_json': {n: n for n in structure}})
            self.__es__ = e
        else:
            super().__init__(**kwargs)

    def get_effective_paths(self, target: 'Complex', limit: int = 10):
        if not limit:
            raise ValueError('limit should be positive')
        paths = []
        for n, path in enumerate(self.search_path(target, limit)):
            nodes = []
            costs = []
            total = 0
            for i, (node, barrier) in enumerate(path, start=1):
                nodes.append(node)
                costs.append(barrier) if i % 2 == 0 else costs.append(0)
                total += costs[-1]
            paths.append(weighted_path(nodes, costs, total))
            if n == 30:
                return paths
        return paths

    def search_path(self, target: 'Complex', max_len=10):
        seen = set()
        seen.add(self)
        final_compl = set()
        final_compl.add(target)
        cur_compl = seen - final_compl
        final_compl -= seen
        if not final_compl:
            return
        queue = []
        n = count()
        for x in cur_compl:
            heappush(queue, (1, 0, next(n), [(x, 0)]))
        old_len = 1
        new_seen = set()
        while queue:
            level, prev_barrier, _, init_path = heappop(queue)
            cur = init_path[-1][0]
            if len(init_path) != old_len:
                seen.update(new_seen)
                old_len = len(init_path)
            cur_len = len(init_path) + 1 < max_len
            for i, r in enumerate(cur.reactant.all()):
                barrier = (r.energy - cur.energy)  # * 627.51
                # barrier = barrier if barrier > prev_barrier else prev_barrier
                prod = r.product.all()[0]
                if prod in final_compl:
                    path = init_path.copy()
                    path.append((r, barrier))
                    path.append((prod, barrier))
                    yield path
                elif cur_len and prod not in seen:
                    new_seen.add(prod)
                    path = init_path.copy()
                    path.append((r, barrier))
                    path.append((prod, barrier))
                    heappush(queue, (len(path), barrier, next(n), path))

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

    def depict3d(self, index: int = 0) -> str:
        s = self.structure
        es = self.equilibrium_states.all()[index]
        mapping = self.equilibrium_states.relationship(es).mapping
        s._conformers.append({mapping[n]: v for n, v in es.xyz.items()})
        return s.depict3d()

    def view3d(self, index: int = 0, width='600px', height='400px'):
        """
        Jupyter widget for 3D visualization.

        :param index: index of conformer
        :param width: widget width
        :param height: widget height
        """
        return JupyterWidget(self.depict3d(index), width, height)

    def _repr_svg_(self):
        return self.depict()

    def __str__(self):
        return str(self.structure)

    __es__ = None  # ad-hoc for storing associated ES


class EquilibriumState(Mixin, StructuredNode, metaclass=ExtNodeMeta):
    xyz_json = JSONProperty()
    energy = FloatProperty()
    signature = StringProperty(unique_index=True, required=True)  # signature of EQ
    complex = RelationshipTo('Complex', 'E2C', cardinality=One, model=Mapping)
    transition_states = RelationshipTo('TransitionState', 'E2T', model=Barrier)

    def __init__(self, structure: MoleculeContainer = None, **kwargs):
        if structure is not None:
            xyz = structure._conformers[0]
            energy = structure.meta['energy']
            signature = [None] * len(structure)
            for n, m in structure.atoms_order.items():
                signature[m - 1] = [round(x, 4) for x in xyz[n]]
            signature = str(signature)
            super().__init__(xyz_json=xyz, energy=energy, signature=signature)
            try:
                self.save()
            except UniqueProperty:
                self.id = self.nodes.get(signature=signature, lazy=True)  # get id of existing node
                self.refresh()
                if -.000001 < self.energy - energy < .000001:
                    raise ValueError('same EquilibriumState with different energy exists')
        else:
            super().__init__(**kwargs)

    @property
    def xyz(self):
        return {int(k): tuple(v) for k, v in self.xyz_json.items()}


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

            # store TS ans ES's first for validation
            ts = TransitionState(t)
            rc = Complex(r)
            pc = Complex(p)
            re = rc.__es__
            pe = pc.__es__

            cgr = r ^ p
            super().__init__(signature=str(cgr), energy=te)
            try:
                self.save()
            except UniqueProperty:  # reaction already exists
                self.id = self.nodes.get(signature=str(cgr), lazy=True)  # get id of existing node
                self.refresh()

                if self.energy > te:  # lower TS found. update barriers.
                    if self.transition_states.is_connected(ts):
                        raise ValueError('same TransitionState with different energy exists')
                    self.energy = te
                    self.save()
                    self.transition_states.connect(ts, {'mapping_json': next(cgr.get_mapping(self.structure))})

                    # new barriers!
                    self.reactant.relationship(rc).energy = te - rc.energy
                    self.product.relationship(pc).energy = te - pc.energy
                elif not self.transition_states.is_connected(ts):  # skip already connected TS
                    self.transition_states.connect(ts, {'mapping_json': next(cgr.get_mapping(self.structure))})
            else:  # new reaction
                # store relation to Brutto
                self.brutto.connect(Brutto(t))

                # connect reactant and product complexes.
                self.reactant.connect(rc, {'mapping_json': next(rc.structure.get_mapping(r)), 'energy': te - rc.energy})
                self.product.connect(pc, {'mapping_json': next(pc.structure.get_mapping(p)), 'energy': te - pc.energy})

                # connect TS to R
                self.transition_states.connect(ts, {'mapping_json': {n: n for n in t}})

            # connect new TS to new ES`s
            if not ts.equilibrium_states.is_connected(re):  # skip already connected TS-ES
                ts.equilibrium_states.connect(re, {'energy': te - re.energy})
            if not ts.equilibrium_states.is_connected(pe):  # skip already connected TS-ES
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

    def depict3d(self, index: int = 0) -> str:
        s = self.structure
        ts = self.transition_states.all()[index]
        mapping = self.transition_states.relationship(ts).mapping
        s._conformers.append({mapping[n]: v for n, v in ts.xyz.items()})
        return s.depict3d(index)

    def view3d(self, index: int = 0, width='600px', height='400px'):
        """
        Jupyter widget for 3D visualization.

        :param index: index of conformer
        :param width: widget width
        :param height: widget height
        """
        return JupyterWidget(self.depict3d(index), width, height)

    def _repr_svg_(self):
        return self.depict()

    def __str__(self):
        return str(self.structure)


class TransitionState(Mixin, StructuredNode, metaclass=ExtNodeMeta):
    xyz_json = JSONProperty()
    energy = FloatProperty()
    signature = StringProperty(unique_index=True, required=True)  # signature of TS
    reaction = RelationshipTo('Reaction', 'T2R', cardinality=One, model=Mapping)
    equilibrium_states = RelationshipFrom('EquilibriumState', 'E2T', model=Barrier)

    def __init__(self, structure: MoleculeContainer = None, **kwargs):
        if structure is not None:
            xyz = structure._conformers[0]
            energy = structure.meta['energy']
            signature = [None] * len(structure)
            for n, m in structure.atoms_order.items():
                signature[m - 1] = [round(x, 4) for x in xyz[n]]
            signature = str(signature)
            super().__init__(xyz_json=xyz, energy=energy, signature=signature)
            try:
                self.save()
            except UniqueProperty:
                self.id = self.nodes.get(signature=signature, lazy=True)  # get id of existing node
                self.refresh()
                if -.000001 < self.energy - energy < .000001:
                    raise ValueError('same TransitionState with different energy exists')
        else:
            super().__init__(**kwargs)

    @property
    def xyz(self):
        return {int(k): tuple(v) for k, v in self.xyz_json.items()}


__all__ = ['Molecule', 'Reaction', 'EquilibriumState', 'TransitionState', 'Barrier', 'Mapping', 'Complex', 'Brutto']
