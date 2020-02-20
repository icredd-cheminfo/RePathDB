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
from CGRdb import Molecule, Reaction
from CGRtools import MoleculeContainer, ReactionContainer
from collections import namedtuple
from pony.orm import db_session
from .graph import Molecule as gMolecule, Reaction as gReaction, EquilibriumState, TransitionState
from .parser import log_parser


equilibrium_data = namedtuple('EquilibriumGate', ['g_mol', 'g_eq', 'mol', 'energy'])


def load_data(eq_file, ts_file, pt_file):
    nodes = {}
    for log in log_parser(eq_file):
        nodes[log.index] = put_equilibrium(log.mol, log.energy)
    if ts_file:
        for log in log_parser(ts_file):
            ts = put_transition(log.mol, log.energy, True, nodes[log.links[0]], nodes[log.links[1]])
            put_reaction(ts, nodes[log.links[0]], nodes[log.links[1]])
            put_reaction(ts, nodes[log.links[1]], nodes[log.links[0]])
    if pt_file:
        for log in log_parser(pt_file):
            ts = put_transition(log.mol, log.energy, False, nodes[log.links[0]], nodes[log.links[1]])
            put_reaction(ts, nodes[log.links[0]], nodes[log.links[1]])
            put_reaction(ts, nodes[log.links[1]], nodes[log.links[0]])


def put_equilibrium(mol: MoleculeContainer, energy: float) -> equilibrium_data:
    """
    Push equilibrium state into both databases
    """
    xyz = mol._conformers[0]

    with db_session:
        found = Molecule.find_structure(mol)
        if not found:
            found = Molecule(mol)
            mapping = {x: x for x in xyz}
        else:
            mapping = next(mol.get_mapping(found.structure))
    # push to graph
    m = gMolecule(cgrdb=found.id).save()
    e = EquilibriumState(xyz=xyz, energy=energy).save()
    rel = e.molecule.connect(m)
    rel.mapping = mapping
    rel.save()
    return equilibrium_data(m, e, mol, energy)


def put_transition(mol: MoleculeContainer, energy: float, true_ts: bool, reactant: equilibrium_data,
                   product: equilibrium_data) -> TransitionState:
    """
    Push transition state into both databases
    """
    xyz = mol._conformers[0]

    ts_node = TransitionState(xyz=xyz, energy=energy, true_ts=true_ts).save()
    # connect equilibra state to transition state node (ES1 -> TS)
    rel = reactant.g_eq.transition_states.connect(ts_node)
    # add energy to connection ES1 -> TS
    rel.energy = energy - reactant.energy
    rel.save()
    # connect equilibra state to transition state node (ES2 -> TS)
    rel = product.g_eq.transition_states.connect(ts_node)
    # add energy to connection ES2 -> TS
    rel.energy = energy - product.energy
    rel.save()
    return ts_node


def put_reaction(ts_node: TransitionState, reactant: equilibrium_data, product: equilibrium_data) -> gReaction:
    """
    Push reaction into both databases
    """

    reaction = ReactionContainer(reactants=[reactant.mol], products=[product.mol])
    with db_session:
        found = Reaction.find_structure(reaction)
        if not found:
            found = Reaction(reaction)
            mapping = {x: x for x in ts_node.xyz}
        else:
            mapping = next((~reaction).get_mapping(found.cgr))

    # create cgr node (CGR)
    r = gReaction(cgrdb=found.id).save()
    # connect cgrnode to ts (CGR -> TS)
    rel = ts_node.reaction.connect(r)
    # add map to relation CGR -> TS
    rel.mapping = mapping
    rel.save()
    # connect mol node to CGR node (MOL -> CGR)
    reactant.g_mol.product.connect(r)
    # connect mol node to CGR node (MOL -> CGR)
    product.g_mol.reactant.connect(r)
    return r


__all__ = ['load_data']
