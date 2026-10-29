from fractions import Fraction
import itertools
import random
import unittest

from tensor_contraction import (ContractionPolicy, Packet, Packing, TensorContraction,
                                 WorkBudget, cauchy_entry, hermite_data,
                                 hermite_recover, pack_network, precision_for_node)
from tensor_network import BooleanNetwork, ConstraintBuilder, Tensor
from tensor_ring import UnramifiedRing, interpolate_low


def table_tensor(side, ports, values):
    return Tensor(side, tuple(ports), lambda bits: values[sum(bit << i for i, bit in enumerate(bits))])


def independent_count(network):
    return sum(__import__('math').prod(t.entry(tuple((assignment >> edge) & 1 for edge in t.ports))
                                      for t in network.tensors)
               for assignment in range(1 << network.edges))


class RingTests(unittest.TestCase):
    def test_inverse_lifting_and_canonical_lifts(self):
        rng = random.Random(8)
        for precision in (1, 3, 9, 37):
            ring = UnramifiedRing(4, precision)
            for _ in range(20):
                value = tuple(rng.randrange(1 << precision) for _ in range(4))
                if not any(c & 1 for c in value):
                    continue
                self.assertEqual(ring.mul(value, ring.inv(value)), ring.one)
                other = tuple(rng.randrange(1 << precision) for _ in range(4))
                self.assertEqual(ring.mul(value, other), ring.mul(other, value))
        ring = UnramifiedRing(4, 9)
        self.assertEqual(ring.lift_from((-1, 4, 0, 0), 2), (3, 0, 0, 0))

    def test_extension_interpolation(self):
        ring = UnramifiedRing(4, 11)
        coefficients = [ring.coerce(9), ring.residue_point(3), ring.coerce(7), ring.residue_point(12)]
        nodes = [ring.residue_point(i) for i in range(4)]
        values = []
        for node in nodes:
            value = ring.zero
            for coefficient in reversed(coefficients):
                value = ring.add(ring.mul(value, node), coefficient)
            values.append(value)
        self.assertEqual(interpolate_low(nodes, values, ring, 4), coefficients)


class DeformationTests(unittest.TestCase):
    def test_cauchy_integrality_against_rational_arithmetic(self):
        ring = UnramifiedRing(4, 13)
        for a in (1, 2):
            L, alpha = 1 << a, 1 << (a + 1)
            denominator = __import__('math').prod(-q for q in range(-L, L) if q)
            for node, x, y, z in itertools.product(range(-L, L), range(L), range(L), (0, 1, -1, 2)):
                T = node + alpha * z
                rational = Fraction(__import__('math').prod(T - q for q in range(-L, L) if q != y - x), denominator)
                self.assertEqual(cauchy_entry(a, node, x, y, ring.coerce(z), ring), ring.fraction(rational))

    def test_tapered_hermite_recovery(self):
        a, u, M, p = 2, 2, 3, 9
        multiplicities = hermite_data(a, u, M)
        coefficients = [(-1) ** i * (i + 3) for i in range(M * (2 * (1 << a) - 1) + 1)]
        for tight in (False, True):
            jets, rings = {}, {}
            for node, q in multiplicities.items():
                pt = precision_for_node(a, u, M, p, node, multiplicities, tight)
                ring = UnramifiedRing(4, pt)
                jet = []
                for j in range(q):
                    value = sum(c * __import__('math').comb(i, j) * node ** (i - j)
                                for i, c in enumerate(coefficients) if i >= j) * (1 << (a + 1)) ** j
                    jet.append(ring.coerce(value))
                jets[node], rings[node] = jet, ring
            self.assertEqual(hermite_recover(a, multiplicities, jets, rings, UnramifiedRing(4, p)),
                             UnramifiedRing(4, p).coerce(coefficients[0]))

    def test_mode_child_identity_against_direct_deformation(self):
        network = BooleanNetwork((table_tensor(0, [0], [1, 3]), table_tensor(0, [1], [2, 5]),
                                  table_tensor(1, [0], [3, 7]), table_tensor(1, [1], [5, 1])))
        packing = Packing(((0,), (1,), (1,), (0,)), (Packet(((0, 1),), (0, 1)),), 0)
        for coalesce in (False, True):
            for precision in (3, 7):
                ring = UnramifiedRing(4, precision)
                engine = TensorContraction(ContractionPolicy(experimental=True, max_depth=1,
                                                             coalesce_modes=coalesce), WorkBudget(1000000, 30))
                engine.root_size, engine.lam, engine.H = 4, 2, 0
                for node in (-1, 1):
                    zeta = ring.residue_point(3)
                    expected = ring.zero
                    for X in itertools.product((0, 1), repeat=2):
                        for Y in itertools.product((0, 1), repeat=2):
                            value = ring.coerce((1, 3)[Y[0]] * (2, 5)[Y[1]] * (3, 7)[X[0]] * (5, 1)[X[1]])
                            for x in range(2):
                                linear = ring.zero
                                for y in range(2):
                                    if X[y]:
                                        linear = ring.add(linear, cauchy_entry(1, node, x, y, zeta, ring))
                                value = ring.mul(value, linear if Y[x] else ring.sub(ring.one, linear))
                            expected = ring.add(expected, value)
                    actual = engine.evaluate_deformation(network.bind_precision(precision), packing, node, zeta, ring)
                    self.assertEqual(actual, expected)


class ContractionTests(unittest.TestCase):
    def test_recursive_engine_matches_exhaustive_count(self):
        network = BooleanNetwork((table_tensor(0, [0], [1, 2]), table_tensor(0, [1], [2, 3]),
                                  table_tensor(1, [0], [3, 4]), table_tensor(1, [1], [5, 1])))
        labels = ((0,), (1,), (1,), (0,))
        for tight in (False, True):
            for coalesce in (False, True):
                policy = ContractionPolicy(experimental=True, groups=2, max_depth=1, leaf_edges=0,
                                            tight_precision=tight, coalesce_modes=coalesce)
                engine = TensorContraction(policy, WorkBudget(2000000, 30))
                actual = engine.contract(network, precision=8, labels_override=labels)
                self.assertEqual(actual, independent_count(network) % 256)
                self.assertGreater(engine.stats['recursive_calls'], 0)
                self.assertGreater(engine.stats['mode_tuples'], 0)

    def test_default_parameter_fallback(self):
        network = BooleanNetwork((table_tensor(0, [0], [1, 1]), table_tensor(1, [0], [1, 1])))
        engine = TensorContraction()
        self.assertEqual(engine.contract(network), 2)
        self.assertEqual(engine.root_plan['root_u'], 0)
        self.assertEqual(engine.stats['recursive_calls'], 0)

    def test_packing_orientation_and_conditional_expectation(self):
        network = BooleanNetwork((table_tensor(0, [0, 1], [1] * 4), table_tensor(0, [2, 3], [1] * 4),
                                  table_tensor(1, [0, 2], [1] * 4), table_tensor(1, [1, 3], [1] * 4)))
        packing = pack_network(network, 2, 2, WorkBudget())
        ends = network.endpoints()
        found = []
        for packet in packing.packets:
            for slot, edge in enumerate(packet.slots):
                if edge is None:
                    continue
                found.append(edge)
                left, right = ends[edge]
                for coordinate, (low, high) in enumerate(packet.pairs):
                    if low != high:
                        bit = (slot >> coordinate) & 1
                        self.assertEqual(packing.labels[left][coordinate], (low, high)[bit])
                        self.assertEqual(packing.labels[right][coordinate], (high, low)[bit])
        self.assertEqual(sorted(found), list(range(4)))

    def test_constraint_builder_counts_and_witness(self):
        builder = ConstraintBuilder()
        x, y, z = [builder.bit() for _ in range(3)]
        # Deliberately nonallocation port order, repeated occurrences, fanout.
        builder.constraint((z, x, y), lambda b: b[0] == (b[1] ^ b[2]))
        builder.constraint((y, x), lambda b: b[0] or b[1])
        builder.constraint((x, x), lambda b: b[0] == b[1])
        network, mapping = builder.compile((x, y, z))
        engine = TensorContraction(budget=WorkBudget(5000000, 30))
        self.assertEqual(engine.contract(network, precision=4), 3)
        witness = engine.witness(network, [mapping[v] for v in (x, y, z)], precision=4)
        self.assertEqual(witness[2], witness[0] ^ witness[1])
        self.assertTrue(witness[0] or witness[1])


if __name__ == '__main__':
    unittest.main(verbosity=2)
