"""Prime-field correctness controls; no performance or challenge-solve claims."""

from copy import deepcopy
import json
import os
from pathlib import Path
import random
import stat
import tempfile
import time
import unittest

from ecc2k import FactorBase, Instance, atomic_json, parameters, solve_hashed, verify_certificate
from eccp import PrimeCurve, PrimeField, PrimeInstance, challenge, toy, validate
from tensor_encoding import bits_value
from tensor_prime import PrimeCurveEncoding
from test_ecc2k import openssl_multiply


def point_inputs(encoding, pairs):
    return {word: value for point, actual in pairs
            for word, value in zip(point.words, encoding.values(actual))}


class PrimeArithmeticTests(unittest.TestCase):
    def test_square_roots_and_canonical_compression(self):
        for p in (5, 7, 17, 41):
            f = PrimeField(p)
            for value in range(p):
                roots = [x for x in range(p) if x * x % p == value]
                actual = f.sqrt(value)
                self.assertEqual(actual is None, not roots)
                if actual is not None:
                    self.assertIn(actual, roots)
        c = PrimeCurve(PrimeField(5), 1, 0)
        self.assertEqual(c.decode(0), (0, 0))
        self.assertIsNone(c.decode(1))  # No second encoding of a y=0 point.
        self.assertIsNone(c.add((0, 0), (0, 0)))
        for c in (c, toy().curve):
            decoded = [c.decode(z) for z in range(2 * c.field.size)]
            points = [P for P in decoded if P is not None]
            self.assertEqual(len(points), len(set(points)))
            for z, P in enumerate(decoded):
                if P is not None:
                    self.assertEqual(c.encode(P), z)
            self.assertIsNone(c.decode(2 * c.field.size))
        with self.assertRaises(ValueError):
            PrimeField(15)
        with self.assertRaises(ValueError):
            PrimeCurve(PrimeField(5), 0, 0)

    def test_official_parameters_cardinality_and_serialization(self):
        instance = challenge()
        result = validate(instance)
        self.assertTrue(all(result['checks'].values()))
        self.assertEqual(instance.order.bit_length(), 131)
        self.assertEqual(instance.curve.field.degree, 131)
        self.assertEqual(instance.cofactor, 1)
        self.assertEqual(Instance.from_dict(instance.as_dict()), instance)
        self.assertEqual(Instance.from_dict(instance.as_dict()).fingerprint, instance.fingerprint)
        invalid = instance.as_dict()
        invalid['cofactor'] = 2
        with self.assertRaises(ValueError):
            validate(PrimeInstance.from_dict(invalid))

    def test_openssl_published_point_multiples(self):
        instance = challenge()
        for point in (instance.P, instance.Q):
            for scalar in (0, 1, 2, 3, 17, 0x123456789ABCDEF012345, instance.order - 1, instance.order):
                self.assertEqual(instance.curve.mul(scalar, point), openssl_multiply(instance, scalar, point))

    def test_inverse_hash_enumeration_matches_entire_subgroup(self):
        instance = toy()
        settings = parameters(instance, 2)
        base = FactorBase.build(instance, int(settings['hash_prime']), 11, random.Random(2), time.monotonic() + 10)
        expected = {instance.curve.mul(k, instance.P) for k in range(1, instance.order)
                    if base.contains_encoding(instance.curve.encode(instance.curve.mul(k, instance.P)))}
        self.assertEqual(set(base.points), expected)

    def test_indexed_tensor_solve_and_corrupted_certificate(self):
        result = solve_hashed(toy(7), slots=2, seed=1, backend='tensor_indexed', seconds=20)
        self.assertEqual(result['scalar'], '7')
        self.assertEqual(verify_certificate(result)['status'], 'verified')
        self.assertFalse(result['subexponential_runtime_claimed'])
        damaged = deepcopy(result)
        damaged['relations'][0]['u'] = str((int(damaged['relations'][0]['u']) + 1) % 19)
        with self.assertRaises(ValueError):
            verify_certificate(damaged)

    def test_atomic_results_have_owner_only_permissions(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'result.json'
            path.write_text('{}')
            path.chmod(0o644)
            old_umask = os.umask(0)
            try:
                atomic_json(path, {'fixture': 7})
            finally:
                os.umask(old_umask)
            self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)
            self.assertEqual(json.loads(path.read_text()), {'fixture': 7})
            self.assertEqual(list(Path(directory).iterdir()), [path])


class PrimeEncodingTests(unittest.TestCase):
    def test_modular_arithmetic_exhaustive_and_tamper_controls(self):
        encoding = PrimeCurveEncoding(toy().curve)
        c, p, width = encoding.circuit, 17, 5
        left, right = c.word(width), c.word(width)
        outputs = [encoding.fp_add(left, right), encoding.fp_sub(left, right), encoding.fp_mul(left, right)]
        for a in range(p):
            for b in range(p):
                values = c.assignment({left: a, right: b})
                actual = [bits_value([values[v] for v in word]) for word in outputs]
                self.assertEqual(actual, [(a + b) % p, (a - b) % p, a * b % p])
                self.assertFalse(c.check(values))
        values = c.assignment({left: 16, right: 16})
        for word in outputs:
            changed = dict(values)
            changed[word[0]] ^= 1
            self.assertTrue(c.check(changed))
        # A noncanonical input must be rejected even if its modular image exists.
        values = c.assignment({left: 17, right: 1})
        self.assertTrue(c.check(values))

    def test_all_small_point_pairs_including_identity(self):
        instance = toy()
        curve = instance.curve
        points = [curve.mul(k, instance.P) for k in range(instance.order)]
        encoding = PrimeCurveEncoding(curve)
        left, right = encoding.point(), encoding.point()
        result = encoding.add(left, right)
        for P in points:
            for Q in points:
                values = encoding.circuit.assignment(point_inputs(encoding, ((left, P), (right, Q))))
                self.assertFalse(encoding.circuit.check(values), (P, Q))
                decoded = encoding.decoded(tuple(bits_value([values[v] for v in word]) for word in result.words))
                self.assertEqual(decoded, curve.add(P, Q))
        changed = dict(values)
        changed[result.infinity[0]] ^= 1
        self.assertTrue(encoding.circuit.check(changed))

    def test_y_zero_doubling_and_fixed_cofactor_image(self):
        curve = PrimeCurve(PrimeField(5), 0, 1)  # Six points; order-three subgroup.
        encoding = PrimeCurveEncoding(curve)
        point = encoding.point()
        doubled = encoding.add(point, point)
        values = encoding.circuit.assignment(point_inputs(encoding, ((point, (4, 0)),)))
        self.assertFalse(encoding.circuit.check(values))
        self.assertEqual(values[doubled.infinity[0]], 1)
        encoding = PrimeCurveEncoding(curve)
        point = encoding.point()
        encoding.in_subgroup_image(point, 3, 2)
        for actual, valid in (((0, 1), True), ((4, 0), False)):
            values = encoding.circuit.assignment(point_inputs(encoding, ((point, actual),)))
            self.assertEqual(not encoding.circuit.check(values), valid)

    def test_coordinate_relation_hash_and_wrong_target_rejection(self):
        instance, prime = toy(), 37
        actual = [instance.P, instance.curve.add(instance.Q, instance.curve.neg(instance.P))]
        seeds = [{'prime': prime, 'alpha': alpha, 'beta': -alpha * instance.curve.encode(P) % prime, 'threshold': 1}
                 for alpha, P in zip((3, 11), actual)]
        encoding = PrimeCurveEncoding(instance.curve)
        points = encoding.relation(instance.Q, seeds, instance.order, instance.cofactor)
        values = encoding.circuit.assignment(point_inputs(encoding, zip(points, actual)))
        self.assertFalse(encoding.circuit.check(values))
        interface = tuple(v for point in points for word in point.words for v in word)
        network, mapping = encoding.circuit.builder.compile(interface)
        self.assertEqual(network.edges, encoding.circuit.statistics(interface)['boolean_network_edges'])
        self.assertTrue(all(v in mapping for v in interface))
        # Valid group coordinates that violate both the hash and the target.
        invalid = encoding.circuit.assignment(point_inputs(encoding, zip(points, [instance.P, instance.P])))
        self.assertTrue(encoding.circuit.check(invalid))
        self.assertTrue(any(name == 'equal' for name in encoding.circuit.check(invalid)))

    def test_challenge_width_products_and_point_branches(self):
        instance = challenge()
        encoding = PrimeCurveEncoding(instance.curve)
        left, right = encoding.point(), encoding.point()
        result = encoding.add(left, right)
        for P, Q in ((instance.P, instance.Q), (instance.P, instance.P),
                     (instance.P, instance.curve.neg(instance.P)), (None, instance.Q)):
            values = encoding.circuit.assignment(point_inputs(encoding, ((left, P), (right, Q))))
            self.assertFalse(encoding.circuit.check(values))
            decoded = encoding.decoded(tuple(bits_value([values[v] for v in word]) for word in result.words))
            self.assertEqual(decoded, instance.curve.add(P, Q))


if __name__ == '__main__':
    unittest.main(verbosity=2)
