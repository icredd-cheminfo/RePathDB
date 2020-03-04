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
from os import listdir
from os.path import join
from pony.orm import db_session, flush
from .graph import Molecule as gMolecule, Reaction as gReaction, EquilibriumState, TransitionState
from .parser import log_parser


equilibrium_data = namedtuple('EquilibriumGate', ['g_mol', 'g_eq', 'mol', 'energy'])


def load_data(files, suffix):
    for f in sorted(listdir(files)):
        if not f.endswith(suffix):
            continue
        try:
            ts, es1, es2 = log_parser(open(join(files, f)))
        except ValueError:
            print(f'invalid: {f}')
            continue

        ed1 = put_equilibrium(es1.mol, es1.energy)
        ed2 = put_equilibrium(es2.mol, es2.energy)
        ts = put_transition(ts.mol, ts.energy, ts.type == 'TS', ed1, ed2)
        put_reaction(ts, ed1, ed2)
        put_reaction(ts, ed2, ed1)
        print(f'processed: {f}')


def put_equilibrium(mol: MoleculeContainer, energy: float) -> equilibrium_data:
    """
    Push equilibrium state into both databases
    """
    xyz = mol._conformers[0]

    with db_session:
        found = Molecule.find_structure(mol)
        if not found:
            mol.clean2d()
            found = Molecule(mol)
            flush()
            m = gMolecule(cgrdb=found.id).save()
            mapping = {x: x for x in xyz}
        else:
            m = gMolecule.nodes.get(cgrdb=found.id)
            mapping = next(mol.get_mapping(found.structure))
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
    barrier = ts_node.energy-reactant.energy
    with db_session:
        found = Reaction.find_structure(reaction)
        if not found:
            found = Reaction(reaction)
            flush()
            # create cgr node (CGR)
            r = gReaction(cgrdb=found.id, energy=barrier).save()
            mapping = {x: x for x in ts_node.xyz}
        else:
            r = gReaction.nodes.get(cgrdb=found.id)
            mapping = next((~reaction).get_mapping(found.cgr))
            if r.energy > barrier:
                r.energy = barrier
                r.save()
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
