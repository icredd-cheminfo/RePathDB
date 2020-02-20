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
                      RelationshipFrom, One, BooleanProperty)


class Barrier(StructuredRel):
    energy = FloatProperty()


class Gate(StructuredRel):
    mapping = JSONProperty()


class Molecule(StructuredNode):
    cgrdb = IntegerProperty(index=True)

    equilibrium_states = RelationshipTo('EquilibriumState', 'M2E', model=Gate)
    reactant = RelationshipTo('Reaction', 'M2R')
    product = RelationshipFrom('Reaction', 'R2M')


class Reaction(StructuredNode):
    cgrdb = IntegerProperty(index=True)

    transition_states = RelationshipTo('TransitionState', 'R2T', model=Gate)
    reactant = RelationshipFrom('Molecule', 'M2R', cardinality=One)
    product = RelationshipTo('Molecule', 'R2M', cardinality=One)


class EquilibriumState(StructuredNode):
    xyz = JSONProperty()
    energy = FloatProperty()

    molecule = RelationshipFrom('Molecule', 'M2E', cardinality=One, model=Gate)
    transition_states = RelationshipTo('TransitionState', 'E2T', model=Barrier)


class TransitionState(StructuredNode):
    xyz = JSONProperty()
    energy = FloatProperty()
    true_ts = BooleanProperty()

    reaction = RelationshipFrom('Reaction', 'R2T', cardinality=One, model=Gate)
    equilibrium_states = RelationshipFrom('EquilibriumState', 'E2T', model=Barrier)


__all__ = ['Molecule', 'Reaction', 'EquilibriumState', 'TransitionState', 'Barrier', 'Gate']
