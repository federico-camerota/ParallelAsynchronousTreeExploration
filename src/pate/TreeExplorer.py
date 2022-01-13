import os
from queue import PriorityQueue
import ray


class TreeExplorer:
    """
    A class to explore a tree that allows to specify functions to process nodes, generate child nodes and prune branches
    Exploration is performed in a parallel and asynchronous fashion by exploiting Ray

    ...

    Attributes
    ----------
    _nodes_list : queue.PriorityQueue
        PriorityQueue that stores current open nodes for exploration
    _state :
        the current state of the exploration
    __update_state: (new_state, old_state) -> updated_state
        updates the exploration state and returns it
    __pruning_condition: (Node, state) -> bool
        predicate used to assert if a branch should be pruned or not
    __process_node: (Node, state) -> new_state, children_nodes
        process a node and return the resulting new state as well as child nodes


    Methods
    -------

    explore_tree()
        Explores the tree and returns the resulting final state
    """

    def __init__(self, init_state, init_node, update_state, process_node, pruning_condition=lambda n, s: False,
                 n_workers=os.cpu_count()):

        self._nodes_list = PriorityQueue()
        self._nodes_list.put(init_node)

        self._state = init_state
        self.__update_state = update_state
        self.__pruning_condition = pruning_condition
        self.__process_node = ray.remote(process_node)
        self._n_workers = n_workers

        ray.init(ignore_reinit_error=True, num_cpus=self._n_workers)

    def explore_tree(self):

        workers_list = []
        while not self._nodes_list.empty() or len(workers_list) > 0:
            while not self._nodes_list.empty() and len(workers_list) < self._n_workers:
                next_node = self._nodes_list.get()[1]
                if not self.__pruning_condition(next_node, self._state):
                    workers_list.append(self.__process_node.remote(next_node, self._state))

            ready, workers_list = ray.wait(workers_list)
            new_state, child_nodes = ray.get(ready)[0]
            self._state = self.__update_state(new_state, self._state)
            [self._nodes_list.put(child) for child in child_nodes if not self.__pruning_condition(child, self._state)]

        return self._state

    @staticmethod
    def close_ray():
        ray.shutdown()
