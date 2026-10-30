"""Executable scalar (ell=1) version of the October 25 contraction construction.

The default policy uses the manuscript's parameters and exact-summation fallback.
Experimental policies exercise the same deformation/mode/Hermite implementation
at small sizes; they make no subexponential complexity claim. All branches share
an explicit operation and wall-clock budget. No meet-in-the-middle backend is
used by this module.
"""

from dataclasses import dataclass, field
from fractions import Fraction
import itertools
import math
import time

from ecc2k import BudgetExceeded, ceil_root
from tensor_network import BooleanNetwork, Tensor
from tensor_ring import UnramifiedRing, interpolate_low, polynomial_product, valuation2


@dataclass
class WorkBudget:
    max_operations: int = 2000000
    seconds: float = 30
    operations: int = 0
    started: float = field(default_factory=time.monotonic)

    def charge(self, count=1):
        self.operations += count
        if self.operations > self.max_operations:
            raise BudgetExceeded(f"tensor operation budget exhausted ({self.max_operations})")
        if self.operations % 64 == 0 and time.monotonic() - self.started > self.seconds:
            raise BudgetExceeded("tensor wall-clock budget exhausted")

    def check(self):
        if time.monotonic() - self.started > self.seconds:
            raise BudgetExceeded("tensor wall-clock budget exhausted")


@dataclass(frozen=True)
class ContractionPolicy:
    experimental: bool = False
    forced_a: int = 1
    forced_u: int = 1
    groups: int = 64
    max_depth: int | None = None
    leaf_edges: int | None = None
    tight_precision: bool = False
    coalesce_modes: bool = True


@dataclass(frozen=True)
class Packet:
    pairs: tuple[tuple[int, int], ...]
    slots: tuple[int | None, ...]


@dataclass(frozen=True)
class Packing:
    labels: tuple[tuple[int, ...], ...]
    packets: tuple[Packet, ...]
    objective: int


def pack_network(network: BooleanNetwork, a: int, groups: int, budget: WorkBudget,
                 labels_override=None) -> Packing:
    """Conditional-expectation labeling and orientation-compatible slot packing."""
    if a < 1 or groups < 2:
        raise ValueError("invalid packing parameters")
    label_count, L = groups ** a, 1 << a
    endpoints = network.endpoints()
    labels = [None] * len(network.tensors)

    def score():
        # q^2 times E[sum_gamma X_gamma^2]; the omitted constant is fixed.
        budget.charge(len(endpoints) * (len(endpoints) + 1) // 2)
        result = 0
        for e, (left, right) in enumerate(endpoints):
            for f in range(e, len(endpoints)):
                other_left, other_right = endpoints[f]
                product = 1
                for first, second in ((left, other_left), (right, other_right)):
                    if first == second:
                        product *= label_count
                    elif labels[first] is not None and labels[second] is not None:
                        product *= label_count if labels[first] == labels[second] else 0
                result += product * (1 if e == f else 2)
        return result

    if labels_override is not None:
        if len(labels_override) != len(labels):
            raise ValueError("one label is required for each vertex")
        labels = [tuple(value) for value in labels_override]
        if any(len(v) != a or any(not 0 <= symbol < groups for symbol in v) for v in labels):
            raise ValueError("invalid explicit packet labels")
    else:
        loads = [[[0] * groups for _ in range(a)] for _ in range(2)]
        for vertex, tensor in enumerate(network.tensors):
            best = None
            for candidate in itertools.product(range(groups), repeat=a):
                budget.charge()
                labels[vertex] = candidate
                objective = score()
                # A tie break balances each coordinate without altering the
                # conditional-expectation minimizer used in the paper.
                imbalance = sum(2 * loads[tensor.side][i][symbol] * len(tensor.ports)
                                for i, symbol in enumerate(candidate))
                key = objective, imbalance, candidate
                if best is None or key < best[0]:
                    best = key, candidate
            labels[vertex] = best[1]
            for i, symbol in enumerate(best[1]):
                loads[tensor.side][i][symbol] += len(tensor.ports)
    classes = {}
    for edge, (left, right) in enumerate(endpoints):
        classes.setdefault((labels[left], labels[right]), []).append(edge)
    padded_load = ((max(map(len, classes.values()), default=0) + L - 1) // L) * L
    packets = {}
    for (row, column), edges in classes.items():
        pairs = tuple((min(x, y), max(x, y)) for x, y in zip(row, column))
        equal = [i for i, (x, y) in enumerate(pairs) if x == y]
        base_slot = sum((row[i] == pairs[i][1]) << i for i in range(a) if pairs[i][0] != pairs[i][1])
        copies = 1 << len(equal)
        for j, edge in enumerate(edges):
            packet_index, copy = divmod(j, copies)
            slot = base_slot | sum(((copy >> bit) & 1) << coordinate for bit, coordinate in enumerate(equal))
            key = pairs, packet_index
            if key not in packets:
                packets[key] = [None] * L
            if packets[key][slot] is not None:
                raise ArithmeticError("packet slot collision")
            packets[key][slot] = edge
    # Entirely empty padding packets can be omitted: they have no ports.
    result = Packing(tuple(labels), tuple(Packet(key[0], tuple(slots)) for key, slots in packets.items()), score())
    if any(len(edges) > padded_load for edges in classes.values()):
        raise ArithmeticError("incorrect collision-class padding")
    return result


def cauchy_entry(a: int, node: int, row: int, column: int, zeta, ring: UnramifiedRing):
    """W_xy(node + alpha*zeta) after exact cancellation of powers of two."""
    L, alpha = 1 << a, 1 << (a + 1)
    if not (-L <= node < L and 0 <= row < L and 0 <= column < L):
        raise ValueError("invalid Cauchy grid coordinate")
    omitted = column - row
    denominator = math.prod(-q for q in range(-L, L) if q)
    denominator_power = valuation2(denominator)
    odd = denominator >> denominator_power
    result, extracted = ring.one, 0
    for q in range(-L, L):
        if q == omitted:
            continue
        if q == node:
            factor, power = zeta, a + 1
        else:
            power = valuation2(node - q)
            factor = ring.add(ring.coerce((node - q) >> power), ring.scale(zeta, alpha >> power))
        extracted += power
        result = ring.mul(result, factor)
    if extracted < denominator_power:
        raise ArithmeticError("Cauchy integrality cancellation failed")
    return ring.scale(result, (1 << (extracted - denominator_power)) * pow(odd, -1, ring.modulus))


def hermite_data(a: int, u: int, edges: int):
    if not 1 <= u <= a or edges < u:
        raise ValueError("Hermite parameters require 1 <= u <= a and M >= u")
    L = 1 << a
    h = (3 * edges + u - 1) // u
    multiplicities = {t: h * max(0, u - valuation2(t)) for t in range(-L, L) if t}
    return {t: q for t, q in multiplicities.items() if q}


def hermite_multiplier(a: int, multiplicities: dict[int, int], node: int):
    result = Fraction(1)
    for other, multiplicity in multiplicities.items():
        if other != node:
            result *= Fraction(-other, node - other) ** multiplicity
    return result


def precision_for_node(a, u, edges, precision, node, multiplicities, tight=False):
    if tight:
        multiplier = hermite_multiplier(a, multiplicities, node)
        valuation = valuation2(multiplier.numerator) - valuation2(multiplier.denominator)
        loss = max(0, -valuation + (multiplicities[node] - 1) * (a + 1 - valuation2(node)))
        return precision + loss
    h = (3 * edges + u - 1) // u
    D = (1 << a) >> valuation2(node)
    return precision + 8 * h * D + 8 * edges * (a + 1)


def hermite_recover(a: int, multiplicities: dict[int, int], jets: dict,
                    rings: dict, output_ring: UnramifiedRing):
    """Tapered Hermite combination using rational common-denominator arithmetic."""
    alpha, coordinates = 1 << (a + 1), [Fraction(0)] * output_ring.degree
    for node, multiplicity in multiplicities.items():
        ring = rings[node]
        inverse_E = [ring.one] + [ring.zero] * (multiplicity - 1)
        for other, q in multiplicities.items():
            if other == node:
                continue
            linear = ring.fraction(Fraction(alpha, node - other))
            power, series = ring.one, []
            for j in range(multiplicity):
                coefficient = (-1 if j & 1 else 1) * math.comb(q + j - 1, j)
                series.append(ring.scale(power, coefficient))
                power = ring.mul(power, linear)
            inverse_E = polynomial_product(inverse_E, series, ring, multiplicity)
        quotient = polynomial_product(jets[node], inverse_E, ring, multiplicity)
        multiplier, argument = hermite_multiplier(a, multiplicities, node), Fraction(-node, alpha)
        for coefficient in quotient:
            for i, coordinate in enumerate(coefficient):
                coordinates[i] += multiplier * coordinate
            multiplier *= argument
    return tuple(output_ring.fraction(value)[0] for value in coordinates)


@dataclass(frozen=True)
class Mode:
    packet: int
    source: int
    target: int
    weight: int
    source_form: tuple[tuple[int, int], ...]
    row_coefficients: tuple[tuple[int, tuple], ...]


def packet_modes(packing: Packing, node: int, zeta, ring: UnramifiedRing,
                 budget: WorkBudget, coalesce=True):
    a = len(packing.labels[0]) if packing.labels else 1
    L, coordinate = 1 << a, valuation2(node)
    alpha, modes = 1 << (a + 1), []
    for packet_index, packet in enumerate(packing.packets):
        pair = packet.pairs[coordinate]
        if pair[0] == pair[1]:
            continue
        live = [x for x, edge in enumerate(packet.slots) if edge is not None]
        for y0 in range(1 << (coordinate + 1)):
            columns = [y for y in live if y % (1 << (coordinate + 1)) == y0]
            rows = [x for x in live if ((x >> coordinate) & 1) == ((y0 >> coordinate) & 1)]
            if not rows or not columns:
                continue
            # Orientation: row bit zero is the lower symbol; column bit zero
            # is the upper symbol. Equal bits therefore describe crossing ports.
            source = pair[0] if (y0 >> coordinate) & 1 else pair[1]
            target = pair[1] if source == pair[0] else pair[0]
            coefficients, ratios = {}, {}
            for x in rows:
                coefficients[x] = cauchy_entry(a, node, x, y0, zeta, ring)
                power = valuation2(node - y0 + x)
                if power > coordinate:
                    raise ArithmeticError("crossing denominator valuation failed")
                unit = ring.add(ring.coerce((node - y0 + x) >> power), ring.scale(zeta, alpha >> power))
                ratios[x] = ring.scale(ring.inv(unit), 1 << (coordinate + 1 - power))
            for exponent in range(ring.precision - 1):
                budget.charge()
                source_form = tuple((y, pow((y - y0) >> (coordinate + 1), exponent, ring.modulus))
                                    for y in columns)
                source_form = tuple((y, value) for y, value in source_form if value)
                active_coefficients = tuple((x, value) for x, value in coefficients.items() if any(value))
                if source_form and active_coefficients:
                    modes.append(Mode(packet_index, source, target, exponent + 1, source_form, active_coefficients))
                coefficients = {x: ring.mul(value, ratios[x]) for x, value in coefficients.items()}
                if not any(any(value) for value in coefficients.values()):
                    break
    if coalesce:
        merged = {}
        for mode in modes:
            key = mode.packet, mode.source, mode.target, mode.source_form
            if key not in merged:
                merged[key] = mode
            else:
                previous = merged[key]
                values = dict(previous.row_coefficients)
                for row, coefficient in mode.row_coefficients:
                    values[row] = ring.add(values.get(row, ring.zero), coefficient)
                merged[key] = Mode(mode.packet, mode.source, mode.target, min(mode.weight, previous.weight),
                                   mode.source_form, tuple((x, value) for x, value in values.items() if any(value)))
        modes = [mode for mode in merged.values() if mode.row_coefficients]
    return tuple(modes)


def mode_tuples(modes, precision, packing, edges, budget):
    """Polynomial-space enumeration, pruning impossible row degrees."""
    limits = {}
    for index, mode in enumerate(modes):
        # In a packet a targeted mode is chosen by a row at most once.
        limits.setdefault((mode.packet, mode.target), len(mode.row_coefficients))
        limits[mode.packet, mode.target] = max(limits[mode.packet, mode.target], len(mode.row_coefficients))
    # Using all rows of a target is a conservative cap when modes have differing
    # nonzero row supports. A smaller support must not cap other modes.
    for packet_index, packet in enumerate(packing.packets):
        for key in list(limits):
            if key[0] == packet_index:
                supports = set(x for mode in modes if mode.packet == packet_index and mode.target == key[1]
                               for x, _ in mode.row_coefficients)
                limits[key] = len(supports)
    exponents = [0] * len(modes)
    used = {key: 0 for key in limits}

    if not modes:
        yield ()
        return
    # Explicit DFS avoids depending on Python's recursion limit when the number
    # of polynomially many mode variables exceeds a thousand.
    remaining = [precision - 1] + [0] * len(modes)
    degrees, next_exponent = [0] * (len(modes) + 1), [0] * len(modes)
    index = 0
    while index >= 0:
        budget.charge()
        if index == len(modes):
            yield tuple(exponents)
            index -= 1
            mode = modes[index]
            used[mode.packet, mode.target] -= exponents[index]
            next_exponent[index] = exponents[index] + 1
            continue
        mode = modes[index]
        key = mode.packet, mode.target
        maximum = min(remaining[index] // mode.weight, edges - degrees[index], limits[key] - used[key])
        exponent = next_exponent[index]
        if exponent > maximum:
            next_exponent[index] = 0
            index -= 1
            if index >= 0:
                previous = modes[index]
                used[previous.packet, previous.target] -= exponents[index]
                next_exponent[index] = exponents[index] + 1
            continue
        exponents[index] = exponent
        used[key] += exponent
        remaining[index + 1] = remaining[index] - exponent * mode.weight
        degrees[index + 1] = degrees[index] + exponent
        index += 1
        if index < len(modes):
            next_exponent[index] = 0


def packet_tensor_entry(packet_index, packet, group, coordinate, modes, beta,
                        node, zeta, ring, budget):
    a = len(packet.pairs)
    rows = [x for x, edge in enumerate(packet.slots) if edge is not None
            and (packet.pairs[coordinate][0] if not (x >> coordinate) & 1 else packet.pairs[coordinate][1]) == group]
    columns = [y for y, edge in enumerate(packet.slots) if edge is not None
               and (packet.pairs[coordinate][1] if not (y >> coordinate) & 1 else packet.pairs[coordinate][0]) == group]
    ports = tuple((0, x) for x in rows) + tuple((1, y) for y in columns)
    targeted = [i for i, mode in enumerate(modes) if mode.packet == packet_index and mode.target == group and beta[i]]
    sourced = [i for i, mode in enumerate(modes) if mode.packet == packet_index and mode.source == group and beta[i]]
    matrices = {(x, y): cauchy_entry(a, node, x, y, zeta, ring) for x in rows for y in columns}
    coefficients = {i: dict(modes[i].row_coefficients) for i in targeted}

    def entry(bits):
        budget.charge()
        assignments = dict(zip(ports, bits))
        desired = [beta[i] for i in targeted]
        if sum(desired) > len(rows):
            return ring.zero
        factors = []
        for x in rows:
            local = ring.zero
            for y in columns:
                if assignments[1, y]:
                    local = ring.add(local, matrices[x, y])
            sign = 1 if assignments[0, x] else -1
            constant = local if sign == 1 else ring.sub(ring.one, local)
            choices = [(None, constant)] if any(constant) else []
            choices.extend((j, ring.scale(coefficients[i][x], sign))
                           for j, i in enumerate(targeted) if x in coefficients[i])
            factors.append(choices)

        if not rows:
            result = ring.one if not any(desired) else ring.zero
        else:
            result, row = ring.zero, 0
            products = [ring.one] * (len(rows) + 1)
            next_choice, chosen_mode = [0] * len(rows), [None] * len(rows)
            while row >= 0:
                budget.charge()
                finished = row == len(rows)
                if finished and not any(desired):
                    result = ring.add(result, products[row])
                if finished or sum(desired) > len(rows) - row or next_choice[row] >= len(factors[row]):
                    if not finished:
                        next_choice[row] = 0
                    row -= 1
                    if row >= 0:
                        if chosen_mode[row] is not None:
                            desired[chosen_mode[row]] += 1
                        next_choice[row] += 1
                    continue
                mode_index, value = factors[row][next_choice[row]]
                if mode_index is not None and not desired[mode_index]:
                    next_choice[row] += 1
                    continue
                chosen_mode[row] = mode_index
                if mode_index is not None:
                    desired[mode_index] -= 1
                products[row + 1] = ring.mul(products[row], value)
                row += 1
                if row < len(rows):
                    next_choice[row] = 0
        for i in sourced:
            value = sum(coefficient * assignments.get((1, y), 0) for y, coefficient in modes[i].source_form)
            result = ring.mul(result, ring.power(ring.coerce(value), beta[i]))
        return result

    return ports, entry


def child_network(network, packing, group, coordinate, modes, beta, node, zeta, ring, budget):
    retained = [index for index, label in enumerate(packing.labels) if label[coordinate] == group]
    port_map, tensors = {}, []
    for index in retained:
        tensor = network.tensors[index]
        new_ports = []
        for edge in tensor.ports:
            port_map[tensor.side, edge] = len(port_map)
            new_ports.append(port_map[tensor.side, edge])
        tensors.append(tensor.move(0, tuple(new_ports)))
    for packet_index, packet in enumerate(packing.packets):
        ports, entry = packet_tensor_entry(packet_index, packet, group, coordinate, modes, beta,
                                           node, zeta, ring, budget)
        new_ports = tuple(port_map[side, packet.slots[slot]] for side, slot in ports)
        # A zero-port packet can still contribute a nontrivial scalar.
        tensors.append(Tensor(1, new_ports, entry, "packet", ring.precision))
    return BooleanNetwork(tuple(tensors))


class TensorContraction:
    def __init__(self, policy=None, budget=None):
        self.policy = policy or ContractionPolicy()
        self.budget = budget or WorkBudget()
        self.stats = {"calls": 0, "leaves": 0, "recursive_calls": 0, "mode_tuples": 0,
                      "interpolation_values": 0, "max_depth": 0, "max_precision": 0,
                      "experimental_parameters": self.policy.experimental}

    def entry(self, tensor, bits, ring):
        self.budget.charge()
        value = tensor.entry(bits)
        return ring.lift_from(value, tensor.creation_precision or ring.precision)

    def prepare_leaf(self, network):
        parent = list(range(network.edges))

        def root(edge):
            while parent[edge] != edge:
                parent[edge] = parent[parent[edge]]
                edge = parent[edge]
            return edge

        for tensor in network.tensors:
            if tensor.equality and tensor.ports:
                first = root(tensor.ports[0])
                for edge in tensor.ports[1:]:
                    parent[root(edge)] = first
        representatives = {root(edge) for edge in range(network.edges)}
        positions = {edge: i for i, edge in enumerate(sorted(representatives))}
        prepared = [(tensor, tuple(positions[root(edge)] for edge in tensor.ports))
                    for tensor in network.tensors if not tensor.equality]
        return prepared, len(positions), {edge: positions[root(edge)] for edge in range(network.edges)}

    def direct(self, network, ring):
        self.stats["leaves"] += 1
        prepared, variables, mapping = self.prepare_leaf(network)
        remaining = self.budget.max_operations - self.budget.operations
        if variables >= remaining.bit_length():
            raise BudgetExceeded(f"exact tensor leaf has {network.edges} edges and {variables} independent bits (2^{variables} assignments); operation budget is {self.budget.max_operations}")
        total = ring.zero
        for assignment in range(1 << variables):
            self.budget.charge()
            product = ring.one
            for tensor, ports in prepared:
                bits = tuple((assignment >> edge) & 1 for edge in ports)
                product = ring.mul(product, self.entry(tensor, bits, ring))
                if not any(product):
                    break
            total = ring.add(total, product)
        return total

    def boolean_witness(self, network, interface_edges):
        """Boolean-only leaf search, or count self-reduction in recursive mode.

        At an exact-summation leaf, stopping at the first satisfying assignment
        avoids computing a count that is not needed by relation finding.
        """
        plan = self.plan(network.edges, network.edges + 1)
        if self.policy.experimental or plan["paper_recursion_eligible"]:
            return self.witness(network, interface_edges)
        self.root_plan = plan
        self.stats["calls"] += 1
        self.stats["leaves"] += 1
        prepared, variables, mapping = self.prepare_leaf(network)
        for assignment in range(1 << variables):
            self.budget.charge()
            accepted = True
            for tensor, ports in prepared:
                self.budget.charge()
                bits = tuple((assignment >> edge) & 1 for edge in ports)
                value = tensor.entry(bits)
                if value not in (0, 1):
                    raise ValueError("boolean_witness requires Boolean predicates")
                if not value:
                    accepted = False
                    break
            if accepted:
                return tuple((assignment >> mapping[edge]) & 1 for edge in interface_edges)
        return None

    def plan(self, edges, precision, size=None):
        size = max(edges, precision, 2) if size is None else size
        if size < max(edges, precision, 2):
            raise ValueError("size parameter must cover edges and input precision")
        lam = (size - 1).bit_length()
        H = (size + max(1, math.isqrt(lam)) - 1) // max(1, math.isqrt(lam))
        return {"size": size, "lambda": lam, "leaf_threshold": H,
                "root_u": lam // 131072, "root_a": 2 * (lam // 131072),
                "extension_degree": 4 * lam, "groups": 64,
                "paper_recursion_eligible": lam // 131072 >= 1,
                "experimental_parameters": self.policy.experimental}

    def contract(self, network: BooleanNetwork, precision=None, size=None, labels_override=None):
        precision = network.edges + 1 if precision is None else precision
        plan = self.plan(network.edges, precision, size)
        self.root_plan = plan
        self.root_size, self.lam = plan["size"], plan["lambda"]
        self.H = plan["leaf_threshold"] if self.policy.leaf_edges is None else self.policy.leaf_edges
        if (not self.policy.experimental and not plan["paper_recursion_eligible"]
                and network.leaf_variables is not None
                and network.leaf_variables >= self.budget.max_operations.bit_length()):
            self.stats["calls"] += 1
            self.stats["leaves"] += 1
            raise BudgetExceeded(f"paper root u=0: exact leaf has {network.leaf_variables} independent bits; configured budget is {self.budget.max_operations} operations")
        ring = UnramifiedRing(plan["extension_degree"], precision)
        value = self._contract(network.bind_precision(precision), ring, 0, None, labels_override)
        if any(value[1:]):
            raise ArithmeticError("base-ring contraction retained nonzero extension coordinates")
        return value[0]

    def _contract(self, network, ring, depth, parent_edges, labels_override=None):
        self.budget.check()
        self.budget.charge()
        self.stats["calls"] += 1
        self.stats["max_depth"] = max(self.stats["max_depth"], depth)
        self.stats["max_precision"] = max(self.stats["max_precision"], ring.precision)
        if self.policy.experimental:
            u, a, groups = self.policy.forced_u, self.policy.forced_a, self.policy.groups
        else:
            u = (self.lam // 131072) >> depth
            a = 2 * sum((self.lam // 131072) >> j for j in range(depth + 1))
            groups = 64
        direct = (network.edges <= self.H or u < 1 or network.edges < u
                  or (self.policy.max_depth is not None and depth >= self.policy.max_depth)
                  or (parent_edges is not None and network.edges >= parent_edges))
        if direct:
            return self.direct(network, ring)
        L, delta = 1 << a, ceil_root(self.root_size ** 9, 10)
        if not self.policy.experimental:
            arrangements = groups ** (2 * a)
            if (network.degree > delta or network.edges < 2 * arrangements ** 2 * delta
                    or network.edges < L * arrangements or 2 * L > delta):
                return self.direct(network, ring)
        packing = pack_network(network, a, groups, self.budget, labels_override)
        self.stats["recursive_calls"] += 1
        multiplicities = hermite_data(a, u, network.edges)
        jets, rings = {}, {}
        interpolation_count = network.edges * (2 * L - 1) + 1
        if interpolation_count > 1 << ring.degree:
            raise ValueError("extension field too small for interpolation")
        for node, multiplicity in multiplicities.items():
            child_precision = precision_for_node(a, u, network.edges, ring.precision, node,
                                                 multiplicities, self.policy.tight_precision)
            child_ring = ring.at_precision(child_precision)
            nodes = [child_ring.residue_point(index) for index in range(interpolation_count)]
            values = []
            for zeta in nodes:
                self.budget.check()
                self.stats["interpolation_values"] += 1
                values.append(self.evaluate_deformation(network, packing, node, zeta, child_ring, depth))
            jets[node] = interpolate_low(nodes, values, child_ring, multiplicity)
            rings[node] = child_ring
        return hermite_recover(a, multiplicities, jets, rings, ring)

    def evaluate_deformation(self, network, packing, node, zeta, ring, depth=0):
        coordinate = valuation2(node)
        modes = packet_modes(packing, node, zeta, ring, self.budget, self.policy.coalesce_modes)
        total = ring.zero
        groups = sorted({label[coordinate] for label in packing.labels}
                        | {mode.source for mode in modes} | {mode.target for mode in modes})
        for beta in mode_tuples(modes, ring.precision, packing, network.edges, self.budget):
            self.stats["mode_tuples"] += 1
            product = ring.one
            for group in groups:
                child = child_network(network, packing, group, coordinate, modes, beta,
                                      node, zeta, ring, self.budget)
                value = self._contract(child, ring, depth + 1, network.edges)
                product = ring.mul(product, value)
                if not any(product):
                    break
            total = ring.add(total, product)
        return total

    def witness(self, network, interface_edges, precision=None):
        """Recover interface bits by exact counts; no discrete-log oracle."""
        precision = network.edges + 1 if precision is None else precision
        if not self.contract(network, precision):
            return None
        fixed = {}
        for edge in interface_edges:
            if edge in fixed:
                continue
            candidate = {**fixed, edge: 0}
            fixed[edge] = 0 if self.contract(network.fixed(candidate), precision) else 1
        return tuple(fixed[edge] for edge in interface_edges)
