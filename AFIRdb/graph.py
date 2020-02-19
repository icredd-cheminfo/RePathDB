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
from neomodel import (StructuredNode, StructuredRel, IntegerProperty, FloatProperty, JSONProperty, RelationshipTo,
                      RelationshipFrom, One)


class Barrier(StructuredRel):
    energy = FloatProperty()


class Molecule(StructuredNode):
    cgrdb = IntegerProperty(index=True)

    equilibrium_states = RelationshipTo('EquilibriumState', 'M2E')
    reactant = RelationshipTo('Molecule', 'M2R')
    product = RelationshipFrom('Molecule', 'R2M')


class Reaction(StructuredNode):
    cgrdb = IntegerProperty(index=True)

    transition_states = RelationshipTo('TransitionState', 'R2T')
    reactant = RelationshipFrom('Molecule', 'M2R', cardinality=One)
    product = RelationshipTo('Molecule', 'R2M', cardinality=One)


class EquilibriumState(StructuredNode):
    xyz = JSONProperty()
    energy = FloatProperty()

    molecule = RelationshipFrom('Molecule', 'M2E', cardinality=One)
    transition_states = RelationshipTo('TransitionState', 'E2T', model=Barrier)


class TransitionState(StructuredNode):
    xyz = JSONProperty()
    energy = FloatProperty()

    reaction = RelationshipFrom('Reaction', 'R2T', cardinality=One)
    equilibrium_states = RelationshipFrom('EquilibriumState', 'E2T', model=Barrier)


__all__ = ['Molecule', 'Reaction', 'EquilibriumState', 'TransitionState', 'Barrier']
