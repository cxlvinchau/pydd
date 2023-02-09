from typing import Any, Dict, Union, List
import functools
from collections import deque


class BDDVariable:

    def __init__(self, name, var_id, is_primed=False):
        self.name = name
        self.var_id = var_id
        self.is_primed = is_primed

    def __eq__(self, other):
        if isinstance(other, BDDVariable):
            return other.var_id == self.var_id
        return False

    def __hash__(self):
        return self.var_id

    def __str__(self):
        if self.is_primed:
            return f"{self.name}_prime"
        return self.name


class BDD:

    def __init__(self):
        self._variable_ordering: List[BDDVariable] = []
        self._var_id = 0
        self._node_id = 2
        self._node_to_row = dict()
        self._row_to_node = dict()
        self._node_to_var_id: Dict[int, Union[int, float]] = {self.get_one_node(): float("infinity"),
                                                              self.get_zero_node(): float("infinity")}

    def get_one_node(self) -> int:
        """
        Returns 1-node

        Returns
        -------
        int

        """
        return 1

    def get_zero_node(self) -> int:
        """
        Returns 0-node

        Returns
        -------
        int

        """
        return 0

    def create_variable(self, name: Any, is_primed=False) -> BDDVariable:
        """
        Create a new variable

        Returns
        -------
        BDDVariable

        """
        v = BDDVariable(name=name, var_id=self._var_id, is_primed=is_primed)
        self._var_id += 1
        self._variable_ordering.append(v)
        return v

    def get_succs(self, n: int):
        v, n1, n0 = self._node_to_row[n]
        return n1, n0

    @functools.lru_cache
    def get_cofactors(self, n: int, v: BDDVariable):
        """
        Return the cofactors of a BDD node w.r.t. given variable

        Parameters
        ----------
        n: int
            Node of the BDD
        v: BDDVariable
            Variable of BDD

        Returns
        -------
        Tuple[int, int]

        """
        if n == self.get_zero_node() or n == self.get_one_node():
            return n, n
        if v.var_id < self._node_to_var_id[n]:
            return n, n
        return self.get_succs(n)

    def make(self, v: BDDVariable, n1: int, n0: int):
        """
        Create a new node

        Parameters
        ----------
        v: BDDVariable
            Variable
        n1: int
            Node of BDD and 1-successor of node
        n0: int
            Node of BDD and 0-successor of node


        Returns
        -------
        int

        """
        if n1 == n0:
            return n1
        if (v.var_id, n1, n0) in self._row_to_node:
            return self._row_to_node[(v.var_id, n1, n0)]
        self._node_to_row[self._node_id] = (v.var_id, n1, n0)
        self._node_to_var_id[self._node_id] = v.var_id
        self._row_to_node[(v.var_id, n1, n0)] = self._node_id
        self._node_id += 1
        return self._node_id - 1

    @functools.lru_cache
    def ite(self, a: int, b: int, c: int):
        """
        Returns a BDD node representing ``if x then y else z``

        Parameters
        ----------
        a: int
            Node of BDD
        b: int
            Node of BDD
        c: int
            Node of BDD

        Returns
        -------
        int

        """
        if a == self.get_one_node():
            return b
        if a == self.get_zero_node():
            return c

        min_var_id = min(self._node_to_var_id[a],
                         self._node_to_var_id[b],
                         self._node_to_var_id[c])
        min_var = self._variable_ordering[min_var_id]
        a1, a0 = self.get_cofactors(a, min_var)
        b1, b0 = self.get_cofactors(b, min_var)
        c1, c0 = self.get_cofactors(c, min_var)
        w1 = self.ite(a1, b1, c1)
        w0 = self.ite(a0, b0, c0)

        if w0 == w1:
            return w0
        return self.make(min_var, w1, w0)

    def neg(self, a: int):
        return self.ite(a, self.get_zero_node(), self.get_one_node())

    @functools.lru_cache
    def conjunction(self, a: int, b: int):
        if a == self.get_zero_node() or b == self.get_zero_node():
            return self.get_zero_node()
        if a == b and a == self.get_one_node():
            return self.get_one_node()

        min_var_id = min(self._node_to_var_id[a], self._node_to_var_id[b])
        min_var = self._variable_ordering[min_var_id]
        a1, a0 = self.get_cofactors(a, min_var)
        b1, b0 = self.get_cofactors(b, min_var)
        w1 = self.conjunction(a1, b1)
        w0 = self.conjunction(a0, b0)
        return self.make(v=min_var, n1=w1, n0=w0)

    @functools.lru_cache
    def disjunction(self, a: int, b: int):
        if a == self.get_one_node() or b == self.get_one_node():
            return self.get_one_node()
        if a == b and a == self.get_zero_node():
            return self.get_zero_node()

        min_var_id = min(self._node_to_var_id[a], self._node_to_var_id[b])
        min_var = self._variable_ordering[min_var_id]
        a1, a0 = self.get_cofactors(a, min_var)
        b1, b0 = self.get_cofactors(b, min_var)
        w1 = self.disjunction(a1, b1)
        w0 = self.disjunction(a0, b0)
        return self.make(v=min_var, n1=w1, n0=w0)

    @functools.lru_cache
    def pre_image(self, a: int, b: int):
        """
        Returns a BDD node representing the pre-image of ``a`` under ``b``, i.e. ``a`` is a BDD node representing
        a function f(x, x') and ``b`` is BDD node representing a function g(x). The function returns the BDD representing
        ``exists x'. (f(x, x') && g(x'))``.

        This method assumes that the variables and their primed counterparts are interleaved, i.e. the variable ordering
        has to adhere to the following order:

        [x_0, x_0', ... , x_i, x_i', ..., x_n, x_n'] where x_i' is the primed version of x_i.

        Parameters
        ----------
        a: int
            Node of BDD
        b: int
            Node of BDD

        Returns
        -------
        int

        """
        if a == self.get_zero_node() or b == self.get_zero_node():
            return self.get_zero_node()
        if a == self.get_one_node() and b == self.get_one_node():
            return self.get_one_node()

        min_var_id = min(self._node_to_var_id[a], self._node_to_var_id[b])
        min_var = self._variable_ordering[min_var_id]

        if min_var.is_primed:
            min_var_primed = min_var
            a1, a0 = self.get_cofactors(a, min_var_primed)
            w1 = self.pre_image(a1, b)
            w0 = self.pre_image(a0, b)
            return self.disjunction(w1, w0)
        else:
            min_var_primed = self._variable_ordering[min_var_id + 1]

            # Consider 4 different possibilities - where x is the minimum variable and x' its primed counterpart
            a1, a0 = self.get_cofactors(a, min_var)
            b1, b0 = self.get_cofactors(b, min_var)  # Using the unprimed variable avoids renaming
            # x = 1, x' = 1 and x = 1, x' = 0
            a11, a10 = self.get_cofactors(a1, min_var_primed)
            # x = 0, x' = 1 and x = 0, x' = 0
            a01, a00 = self.get_cofactors(a0, min_var_primed)

            w10 = self.pre_image(a10, b0)
            w11 = self.pre_image(a11, b1)
            w00 = self.pre_image(a00, b0)
            w01 = self.pre_image(a01, b1)

            return self.make(v=min_var, n1=self.disjunction(w10, w11), n0=self.disjunction(w00, w01))

    def node_from_variable(self, v: BDDVariable):
        return self.make(v, self.get_one_node(), self.get_zero_node())

    def create_variable_node(self, name, is_primed=False):
        v = self.create_variable(name, is_primed=is_primed)
        return self.node_from_variable(v)

    def clear(self, nodes: List[int]):
        """
        Removes all BDD nodes that are not used for the given nodes

        Parameters
        ----------
        nodes: List[int]

        """
        queue = deque(nodes)
        explored = set()
        while queue:
            current = queue.popleft()
            explored.add(current)
            if current in [self.get_one_node(), self.get_zero_node()]:
                continue
            for n in self.get_succs(current):
                if n not in explored:
                    queue.append(n)

        inactive_nodes = set(self._node_to_row.keys()).difference(explored)
        for node in inactive_nodes:
            del self._node_to_var_id[node]
            row = self._node_to_row[node]
            del self._row_to_node[row]
            del self._node_to_row[node]

    def to_dot(self):
        def node_to_label(n):
            if n == self.get_one_node() or n == self.get_zero_node():
                return str(n)
            return f"{str(self._variable_ordering[self._node_to_var_id[n]])}_id_{n}"

        out = "digraph{\n"
        for n, (v, n1, n0) in self._node_to_row.items():
            if n1 != self.get_zero_node():
                out += f"{str(node_to_label(n))} -> {str(node_to_label(n1))} [label=\"1\"]\n"
            if n0 != self.get_zero_node():
                out += f"{str(node_to_label(n))} -> {str(node_to_label(n0))} [label=\"0\"]\n"
        return out + "}"
