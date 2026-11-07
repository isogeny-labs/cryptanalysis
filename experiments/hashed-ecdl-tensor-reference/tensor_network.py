"""Bipartite Boolean tensor networks with immutable creation-time entries."""

from dataclasses import dataclass, replace
from typing import Callable


@dataclass(frozen=True)
class Tensor:
    side: int
    ports: tuple[int, ...]
    entry: Callable
    name: str = "tensor"
    creation_precision: int | None = None
    equality: bool = False

    def move(self, side: int, ports: tuple[int, ...]):
        return replace(self, side=side, ports=ports)


@dataclass(frozen=True)
class BooleanNetwork:
    tensors: tuple[Tensor, ...]
    leaf_variables: int | None = None

    def __post_init__(self):
        sides = [{}, {}]
        for index, tensor in enumerate(self.tensors):
            if tensor.side not in (0, 1) or len(set(tensor.ports)) != len(tensor.ports):
                raise ValueError("invalid tensor side or repeated port")
            for edge in tensor.ports:
                if edge < 0 or edge in sides[tensor.side]:
                    raise ValueError("each edge must occur once on each side")
                sides[tensor.side][edge] = index
        if sides[0].keys() != sides[1].keys() or set(sides[0]) != set(range(len(sides[0]))):
            raise ValueError("edges must be numbered consecutively with two opposite endpoints")

    @property
    def edges(self):
        return sum(len(t.ports) for t in self.tensors if t.side == 0)

    @property
    def degree(self):
        return max((len(t.ports) for t in self.tensors), default=0)

    def endpoints(self):
        result = [[None, None] for _ in range(self.edges)]
        for index, tensor in enumerate(self.tensors):
            for edge in tensor.ports:
                result[edge][tensor.side] = index
        return tuple(map(tuple, result))

    def bind_precision(self, precision):
        return BooleanNetwork(tuple(replace(t, creation_precision=precision)
                                    if t.creation_precision is None else t for t in self.tensors), self.leaf_variables)

    def fixed(self, assignments: dict[int, int]):
        if any(edge < 0 or edge >= self.edges or bit not in (0, 1) for edge, bit in assignments.items()):
            raise ValueError("invalid fixed edge")
        tensors = []
        for tensor in self.tensors:
            constraints = [(i, assignments[edge]) for i, edge in enumerate(tensor.ports)
                           if tensor.side == 0 and edge in assignments]
            if constraints:
                old = tensor.entry

                def entry(bits, old=old, constraints=tuple(constraints)):
                    return old(bits) if all(bits[i] == bit for i, bit in constraints) else 0

                tensors.append(replace(tensor, entry=entry, equality=False))
            else:
                tensors.append(tensor)
        return BooleanNetwork(tuple(tensors))


class ConstraintBuilder:
    """Compile Boolean constraints and bounded-degree copy trees to a BTN.

    All constraints are implicit predicates. Every wire is subdivided once to
    obtain a bipartite graph, including wires inside the equality trees.
    """

    def __init__(self):
        self.variables = 0
        self.constraints = []

    def bit(self):
        result = self.variables
        self.variables += 1
        return result

    def word(self, size):
        return tuple(self.bit() for _ in range(size))

    def constraint(self, variables, predicate, name="constraint"):
        variables = tuple(variables)
        unique = tuple(dict.fromkeys(variables))
        position_map = {v: i for i, v in enumerate(unique)}
        positions = tuple(position_map[v] for v in variables)

        def entry(bits):
            return int(bool(predicate(tuple(bits[i] for i in positions))))

        self.constraints.append((unique, entry, name))

    def pin(self, variable, value):
        self.constraint((variable,), lambda bits: bits[0] == value, "pin")

    def compile(self, interface=()):
        vertices = []
        occurrences = {v: [] for v in range(self.variables)}
        raw_edges = []
        edge_variables = []
        for variables, predicate, name in self.constraints:
            index = len(vertices)
            vertices.append([[], predicate, name])
            for variable in variables:
                occurrences[variable].append(index)
        # Add an interface occurrence, so fixed edges can name every requested bit.
        interfaces = {}
        for variable in dict.fromkeys(interface):
            index = len(vertices)
            vertices.append([[], lambda bits: 1, "interface"])
            occurrences[variable].append(index)
            interfaces[variable] = index

        def equality(bits):
            return int(not bits or all(bit == bits[0] for bit in bits))

        def connect(left, right):
            edge = len(raw_edges)
            raw_edges.append((left, right))
            edge_variables.append(variable)
            vertices[left][0].append(edge)
            vertices[right][0].append(edge)

        for variable, ends in occurrences.items():
            if not ends:
                # A declared unused bit contributes a factor of two.
                vertices.append([[], lambda bits: 2, "unused_bit"])
            elif len(ends) == 1:
                node = len(vertices)
                vertices.append([[], lambda bits: 1, "free_bit"])
                connect(ends[0], node)
            elif len(ends) == 2:
                connect(ends[0], ends[1])
            else:
                remaining = list(ends)
                while len(remaining) > 2:
                    left, right = remaining.pop(), remaining.pop()
                    node = len(vertices)
                    vertices.append([[], equality, "copy"])
                    connect(left, node)
                    connect(right, node)
                    remaining.append(node)
                connect(*remaining)
        tensors = []
        for index, (ports, predicate, name) in enumerate(vertices):
            # The constraint's original variable order is the occurrence order.
            # Copy-tree connections can be added in a different order: restore it.
            if index < len(self.constraints):
                by_variable = {edge_variables[edge]: edge for edge in ports}
                ports = [by_variable[v] for v in self.constraints[index][0]]
            tensors.append(Tensor(0, tuple(2 * edge + (0 if raw_edges[edge][0] == index else 1)
                                           for edge in ports), predicate, name, equality=predicate is equality))
        for edge in range(len(raw_edges)):
            tensors.append(Tensor(1, (2 * edge, 2 * edge + 1), equality, "subdivision", equality=True))
        mapping = {v: tensors[index].ports[0] for v, index in interfaces.items()}
        return BooleanNetwork(tuple(tensors), sum(bool(ends) for ends in occurrences.values())), mapping
