import random
import unittest

from ecc2k import carryless, challenge, solve_hashed, toy, verify_certificate
from tensor_encoding import BinaryCurveEncoding, WordCircuit, bits_value
from tensor_contraction import ContractionPolicy, TensorContraction, WorkBudget
from tensor_network import BooleanNetwork, Tensor


class ArithmeticEncodingTests(unittest.TestCase):
    def test_fourier_integer_and_binary_multiplication(self):
        for kind in ('integer', 'binary'):
            for width in (3, 7, 19, 131):
                circuit = WordCircuit()
                left, right = circuit.word(width), circuit.word(width)
                result = circuit.integer_multiply(left, right) if kind == 'integer' else circuit.polynomial_multiply(left, right)
                rng = random.Random(width)
                cases = [(0, 0), ((1 << width) - 1, (1 << width) - 1),
                         (rng.randrange(1 << width), rng.randrange(1 << width))]
                for a, b in cases:
                    values = circuit.assignment({left: a, right: b})
                    actual = bits_value([values[v] for v in result])
                    self.assertEqual(actual, a * b if kind == 'integer' else carryless(a, b))
                    self.assertFalse(circuit.check(values))
                if width == 3:
                    network, _ = circuit.builder.compile()
                    self.assertEqual(network.edges, circuit.statistics()['boolean_network_edges'])

    def test_binary_field_products_against_reference_arithmetic(self):
        for instance in (toy(7), toy(13), challenge()):
            f, circuit = instance.curve.field, WordCircuit()
            a, b = circuit.word(f.degree), circuit.word(f.degree)
            result = circuit.gf_multiply(a, b, f)
            for left, right in ((instance.P[0], instance.Q[1]), (0, 1), (f.size - 1, f.size - 1)):
                values = circuit.assignment({a: left, b: right})
                self.assertEqual(bits_value([values[v] for v in result]), f.mul(left, right))
                self.assertFalse(circuit.check(values))
            changed = dict(values)
            variable = next(v for v in result if v not in circuit.constants.values())
            changed[variable] ^= 1
            self.assertTrue(circuit.check(changed))

    def test_binary_point_addition_all_cases(self):
        instance = toy(7)
        P, Q, c = instance.P, instance.Q, instance.curve
        for left, right in ((None, None), (None, P), (P, None), (P, P), (P, c.neg(P)),
                            ((0, 1), (0, 1)), (P, Q)):
            encoding = BinaryCurveEncoding(c)
            a, b = encoding.point(), encoding.point()
            result = encoding.add(a, b)
            inputs = {word: value for point, actual in ((a, left), (b, right))
                      for word, value in zip(point.words, encoding.values(actual))}
            values = encoding.circuit.assignment(inputs)
            actual = encoding.decoded(tuple(bits_value([values[v] for v in word]) for word in result.words))
            self.assertEqual(actual, c.add(left, right))
            self.assertFalse(encoding.circuit.check(values))

    def test_coordinate_relation_and_subgroup_witness(self):
        instance = toy(7)
        actual = [instance.P, instance.curve.add(instance.Q, instance.curve.neg(instance.P))]
        prime = 257
        seeds = [{'prime': prime, 'alpha': alpha,
                  'beta': -alpha * instance.curve.encode(point) % prime, 'threshold': 32}
                 for alpha, point in zip((17, 31), actual)]
        encoding = BinaryCurveEncoding(instance.curve)
        points = encoding.relation(instance.Q, seeds, instance.order, instance.cofactor)
        supplied = {word: value for point, coordinates in zip(points, actual)
                    for word, value in zip(point.words, encoding.values(coordinates))}
        values = encoding.circuit.assignment(supplied)
        self.assertFalse(encoding.circuit.check(values))
        interface = tuple(v for point in points for word in point.words for v in word)
        network, mapping = encoding.circuit.builder.compile(interface)
        stats = encoding.circuit.statistics(interface)
        self.assertEqual(network.edges, stats['boolean_network_edges'])
        self.assertEqual(network.degree, stats['maximum_degree'])
        self.assertTrue(all(v in mapping for v in interface))
        changed = dict(values)
        changed[points[0].x[0]] ^= 1
        self.assertTrue(encoding.circuit.check(changed))


class IntegratedTensorTests(unittest.TestCase):
    def test_hashed_indexed_tensor_pipeline(self):
        result = solve_hashed(toy(7, 19), slots=2, backend='tensor_indexed', seed=1, seconds=10)
        self.assertEqual(result['scalar'], '19')
        self.assertEqual(result['backend'], 'tensor_indexed')
        self.assertFalse(result['subexponential_runtime_claimed'])
        self.assertEqual(verify_certificate(result)['status'], 'verified')

    def test_two_recursive_levels_and_creation_time_lifts(self):
        tensors = []
        for side in (0, 1):
            for edge in range(4):
                entries = (edge + 1, (-1 if side else 2) * (edge + 2))
                tensors.append(Tensor(side, (edge,), lambda bits, entries=entries: entries[bits[0]]))
        network = BooleanNetwork(tuple(tensors))
        expected = 1
        for edge in range(4):
            expected *= (edge + 1) ** 2 - 2 * (edge + 2) ** 2
        policy = ContractionPolicy(experimental=True, groups=4, leaf_edges=0, max_depth=2,
                                   tight_precision=True)
        engine = TensorContraction(policy, WorkBudget(2000000, 30))
        self.assertEqual(engine.contract(network, precision=9), expected % 512)
        self.assertGreater(engine.stats['recursive_calls'], 1)
        self.assertEqual(engine.stats['max_depth'], 2)

    def test_larger_packet_and_tapered_valuation_levels(self):
        network = BooleanNetwork((Tensor(0, (0, 1), lambda b: 1 + b[0] + 2 * b[1]),
                                  Tensor(1, (0, 1), lambda b: 3 - b[0] + b[1])))
        expected = sum((1 + x + 2 * y) * (3 - x + y) for x in (0, 1) for y in (0, 1))
        policy = ContractionPolicy(experimental=True, forced_a=2, forced_u=2, groups=2,
                                   leaf_edges=0, max_depth=1, tight_precision=True)
        engine = TensorContraction(policy, WorkBudget(2000000, 30))
        self.assertEqual(engine.contract(network, precision=8, labels_override=((0, 0), (1, 1))), expected)
        self.assertGreater(engine.stats['interpolation_values'], 14)


if __name__ == '__main__':
    unittest.main(verbosity=2)
