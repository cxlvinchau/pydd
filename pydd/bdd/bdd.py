from typing import Any, Dict, Union
import functools


class BDDVariable:

    def __init__(self, name, var_id):
        self.name = name
        self.var_id = var_id

    def __eq__(self, other):
        if isinstance(other, BDDVariable):
            return other.var_id == self.var_id
        return False

    def __hash__(self):
        return self.var_id

    def __str__(self):
        return self.name


class BDD:

    def __init__(self):
        self._variable_ordering = []
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

    def create_variable(self, name: Any) -> BDDVariable:
        """
        Create a new variable

        Returns
        -------
        BDDVariable

        """
        v = BDDVariable(name=name, var_id=self._var_id)
        self._var_id += 1
        self._variable_ordering.append(v)
        return v

    def get_succs(self, n: int):
        v, n1, n0 = self._node_to_row[n]
        return n1, n0

    @functools.lru_cache
    def get_cofactors(self, n: int, v: BDDVariable):
        """
        Return the cofactor of a BDD node

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
            1-successor of node
        n0: int
            0-successor of node


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
        return self.ite(a, self.get_one_node(), self.get_zero_node())

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
            return self.get_one_node()

        min_var_id = min(self._node_to_var_id[a], self._node_to_var_id[b])
        min_var = self._variable_ordering[min_var_id]
        a1, a0 = self.get_cofactors(a, min_var)
        b1, b0 = self.get_cofactors(b, min_var)
        w1 = self.disjunction(a1, b1)
        w0 = self.disjunction(a0, b0)
        return self.make(v=min_var, n1=w1, n0=w0)

    def create_variable_node(self, name):
        v = self.create_variable(name)
        return self.make(v, self.get_one_node(), self.get_zero_node())

    def to_dot(self):
        def node_to_label(n):
            if n == self.get_one_node() or n == self.get_zero_node():
                return str(n)
            return f"{self._variable_ordering[self._node_to_var_id[n]].name}_{n}"

        out = "digraph{\n"
        for n, (v, n1, n0) in self._node_to_row.items():
            if n1 != self.get_zero_node():
                out += f"{str(node_to_label(n))} -> {str(node_to_label(n1))} [label=\"1\"]\n"
            if n0 != self.get_zero_node():
                out += f"{str(node_to_label(n))} -> {str(node_to_label(n0))} [label=\"0\"]\n"
        return out + "}"
