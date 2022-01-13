import copy
import itertools
import time
from typing import List

import numpy as np


from Istop.AirlineAndFlight.istopFlight import IstopFlight

from Istop.Solvers.bb import BB, Offer
from Istop.Solvers import bb
from Istop.old.bb_old import get_offers_for_flight

import ray
from collections import namedtuple


stop = bb.stop


#### Compatibility mat funcs
def compute_compatibility_mat(n_offers, offers):
        comp_mat = np.full((n_offers, n_offers), False, dtype=bool)

        row_workers = [offer_compatibilities.remote(i, offer, offers) for i, offer in enumerate(offers)]

        comp_rows = ray.get(row_workers)
        for i, idxs in comp_rows:
            comp_mat[i, idxs] = True

@ray.remote
def offer_compatibilities(i, offer, offers):

    incompatible = [off for flight in offer.flights for off in flight.offers]
    indexes = [off.num for off in offers if off not in incompatible]

    return i, indexes

####

#### STATE AND NODE DEFINITIONS
State = namedtuple('State', ['solution', 'reduction', 'reductions', 'compatibility_mat', 'init_solution'])
Node = namedtuple('Node', ['solution', 'offers', 'reduction'])

offers =
reductions =
num_offers =

init_state = State(np.full(num_offers, False), 0, reductions, compute_compatibility_mat(num_offers, offers), False)
init_node = Node(np.full(num_offers, False), np.full(num_offers, True), 0)

####

#### UTIL FUNCTIONS
def update_state(new_state: State, old_state: State):
    return new_state if new_state.reduction > old_state.reduction else old_state

def process_node(node: Node, state: State):

    child_list = [node]
    new_state = state

    node_count = 0
    max_node = 20_000 if np.any(node.solution) else 1000


    while node_count < max_node and len(child_list) > 0:

        current_node = child_list.pop(-1)

        if np.sum(current_node.offers) == 0:
            new_state =  State(current_node.solution, current_node.reduction, None, None, True) if new_state.reduction < current_node.reduction else new_state
            continue

        idx = np.nonzero(current_node.offers)[0][0]

        l_reduction = current_node.reduction + reductions[idx]
        l_solution = copy.copy(current_node.solution)
        l_solution[idx] = True

        if l_reduction > state.reduction:
            new_state = State(l_solution, l_reduction, None, None, state.init_solution)

        l_offers = state.compatibility_mat[idx] * current_node.offers
        l_offers[idx] = False

        if state.init_solution:
            l_offers_reduction = sum(reductions * l_offers)
            bound = l_reduction + l_offers_reduction

            if not bound < new_state.reduction:
                child_list.append(Node(l_solution, l_offers, l_reduction))
        else:
            child_list.append(Node(l_solution, l_offers, l_reduction))

        r_offers = offers
        r_offers[idx] = False

        r_offers_reduction = sum(reductions * r_offers)
        bound = current_node.reduction + r_offers_reduction
        if not bound < new_state.reduction:
            child_list.append(Node(current_node.solution, r_offers, current_node.reduction))

        node_count +=1
    return new_state, child_list

def pruning_condition(node, state):
    return False
####