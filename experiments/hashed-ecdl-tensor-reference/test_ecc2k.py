"""Arithmetic, independent OpenSSL comparisons, and complete solver certificates."""

from copy import deepcopy
import ctypes as ct
import ctypes.util
from dataclasses import replace
import json
from pathlib import Path
import random
import tempfile
import time
import unittest

from ecc2k import (BinaryField, BudgetExceeded, FactorBase, MITMRelations,
                   bsgs, challenge, koblitz_order, parameters, rho,
                   solve_hashed, toy, validate, verify_certificate)


def openssl_multiply(instance, scalar, point):
    """Independent binary/prime-field arithmetic via system OpenSSL."""
    path = ctypes.util.find_library("crypto")
    if path is None:
        raise unittest.SkipTest("system OpenSSL unavailable")
    lib = ct.CDLL(path)
    prime_field = instance.as_dict().get("field_type") == "prime"
    constructor = "EC_GROUP_new_curve_GFp" if prime_field else "EC_GROUP_new_curve_GF2m"
    if not hasattr(lib, constructor):
        raise unittest.SkipTest("system OpenSSL lacks requested curve constructor")
    signatures = {
        "BN_bin2bn": ([ct.c_void_p, ct.c_int, ct.c_void_p], ct.c_void_p),
        "BN_new": ([], ct.c_void_p),
        "BN_free": ([ct.c_void_p], None),
        "BN_bn2binpad": ([ct.c_void_p, ct.c_void_p, ct.c_int], ct.c_int),
        "BN_CTX_new": ([], ct.c_void_p),
        "BN_CTX_free": ([ct.c_void_p], None),
        constructor: ([ct.c_void_p] * 4, ct.c_void_p),
        "EC_GROUP_free": ([ct.c_void_p], None),
        "EC_POINT_new": ([ct.c_void_p], ct.c_void_p),
        "EC_POINT_free": ([ct.c_void_p], None),
        "EC_POINT_set_affine_coordinates": ([ct.c_void_p] * 5, ct.c_int),
        "EC_POINT_get_affine_coordinates": ([ct.c_void_p] * 5, ct.c_int),
        "EC_POINT_mul": ([ct.c_void_p] * 6, ct.c_int),
        "EC_POINT_is_at_infinity": ([ct.c_void_p] * 2, ct.c_int),
    }
    for name, (args, result) in signatures.items():
        function = getattr(lib, name)
        function.argtypes, function.restype = args, result
    bns, points = [], []
    ctx, group = lib.BN_CTX_new(), None

    def bn(value):
        data = value.to_bytes(max(1, (value.bit_length() + 7) // 8), "big")
        buffer = ct.create_string_buffer(data)
        result = lib.BN_bin2bn(buffer, len(data), None)
        if not result:
            raise RuntimeError("OpenSSL BIGNUM allocation failed")
        bns.append(result)
        return result

    try:
        c = instance.curve
        modulus = c.field.size if prime_field else c.field.polynomial
        group = getattr(lib, constructor)(bn(modulus), bn(c.a), bn(c.b), ctx)
        if not group:
            raise unittest.SkipTest("OpenSSL build rejects requested field group")
        source, destination = lib.EC_POINT_new(group), lib.EC_POINT_new(group)
        points.extend([source, destination])
        if lib.EC_POINT_set_affine_coordinates(group, source, bn(point[0]), bn(point[1]), ctx) != 1:
            raise AssertionError("OpenSSL rejected source point")
        if lib.EC_POINT_mul(group, destination, None, source, bn(scalar), ctx) != 1:
            raise AssertionError("OpenSSL multiplication failed")
        if lib.EC_POINT_is_at_infinity(group, destination):
            return None
        x, y = bn(0), bn(0)
        if lib.EC_POINT_get_affine_coordinates(group, destination, x, y, ctx) != 1:
            raise AssertionError("OpenSSL affine conversion failed")
        size = (c.field.degree + 7) // 8
        result = []
        for value in (x, y):
            buffer = ct.create_string_buffer(size)
            if lib.BN_bn2binpad(value, buffer, size) != size:
                raise AssertionError("OpenSSL BIGNUM conversion failed")
            result.append(int.from_bytes(buffer.raw, "big"))
        return tuple(result)
    finally:
        for value in points:
            lib.EC_POINT_free(value)
        if group:
            lib.EC_GROUP_free(group)
        for value in bns:
            lib.BN_free(value)
        lib.BN_CTX_free(ctx)


class ArithmeticTests(unittest.TestCase):
    def test_field_axioms_exhaustive_small_field(self):
        f = BinaryField(7, 0x83)
        self.assertTrue(f.irreducible())
        for a in range(128):
            self.assertEqual(f.square(a), f.mul(a, a))
            self.assertEqual(f.square(f.sqrt(a)), a)
            if a:
                self.assertEqual(f.mul(a, f.inv(a)), 1)
            z = f.quadratic(a)
            solutions = [v for v in range(128) if f.square(v) ^ v == a]
            self.assertEqual(z is not None, bool(solutions))
            if z is not None:
                self.assertIn(z, solutions)
        with self.assertRaises(ZeroDivisionError):
            f.inv(0)
        self.assertFalse(BinaryField(7, 0x81).irreducible())

    def test_complete_small_curve_and_encoding(self):
        c = toy(7).curve
        points = []
        for z in range(c.field.size << 1):
            point = c.decode(z)
            if point is not None:
                self.assertTrue(c.valid(point))
                self.assertEqual(c.encode(point), z)
                self.assertIsNone(c.add(point, c.neg(point)))
                points.append(point)
        self.assertEqual(len(points) + 1, 116)
        self.assertEqual(len(set(points)), 115)
        self.assertEqual(koblitz_order(7), 116)
        rng = random.Random(3)
        for _ in range(50):
            a, b, d = rng.choices(points, k=3)
            self.assertEqual(c.add(c.add(a, b), d), c.add(a, c.add(b, d)))

    def test_published_challenge_parameters(self):
        instance = challenge()
        self.assertTrue(all(validate(instance)["checks"].values()))
        self.assertEqual(instance.curve.field.degree, 131)
        self.assertEqual(instance.order.bit_length(), 130)
        d = json.loads((Path(__file__).parent / "challenge.json").read_text())
        for key, expected in (("U", instance.P), ("V", instance.Q)):
            source = tuple(int(value, 0) for value in d[key])
            self.assertEqual(instance.curve.mul(4, source), expected)

    def test_openssl_independent_challenge_vectors(self):
        instance = challenge()
        for point in (instance.P, instance.Q):
            for scalar in (1, 2, 3, 17, 0x123456789ABCDEF012345, instance.order):
                self.assertEqual(instance.curve.mul(scalar, point), openssl_multiply(instance, scalar, point))

    def test_koblitz_frobenius_relation(self):
        instance = challenge()
        c = instance.curve
        # For a=0, tau^2 + tau + [2] = 0.
        for point in (instance.P, instance.Q):
            self.assertIsNone(c.add(c.add(c.frobenius(c.frobenius(point)), c.frobenius(point)), c.mul(2, point)))
            current = point
            for _ in range(131):
                current = c.frobenius(current)
            self.assertEqual(current, point)


class SolverTests(unittest.TestCase):
    def test_inverse_hash_enumeration_against_exhaustive_membership(self):
        instance = toy(7)
        c = instance.curve
        settings = parameters(instance, 2)
        base = FactorBase.build(instance, int(settings["hash_prime"]), settings["threshold"],
                                random.Random(42), time.monotonic() + 5)
        subgroup = [c.mul(i, instance.P) for i in range(1, instance.order)]
        expected = {point for point in subgroup if base.contains_encoding(c.encode(point))}
        self.assertEqual(set(base.points), expected)
        finder = MITMRelations(c, [base, base], 10000, time.monotonic() + 5)
        sums = {c.add(a, b) for a in base.points for b in base.points}
        for scalar in range(instance.order):
            point = c.mul(scalar, instance.P)
            indices = finder.find(point)
            self.assertEqual(indices is not None, point in sums)
            if indices is not None:
                self.assertEqual(c.add(base.points[indices[0]], base.points[indices[1]]), point)

    def test_hashed_scalar_recovery_and_certificate(self):
        for secret in (1, 19, 723, 1427, 2002):
            instance = toy(13, secret)
            solved = solve_hashed(instance, slots=3, seed=secret, seconds=10)
            self.assertEqual(int(solved["scalar"]), secret)
            self.assertEqual(verify_certificate(solved)["status"], "verified")

    def test_certificate_rejects_tampering(self):
        solved = solve_hashed(toy(13, 1427), seed=4)
        changed = deepcopy(solved)
        changed["scalar"] = str((int(changed["scalar"]) + 1) % 2003)
        with self.assertRaises(ValueError):
            verify_certificate(changed)
        changed = deepcopy(solved)
        changed["relations"][0]["u"] = str(int(changed["relations"][0]["u"]) + 1)
        with self.assertRaises(ValueError):
            verify_certificate(changed)
        changed = deepcopy(solved)
        changed["dependency"] = {"0": "1"}
        with self.assertRaises(ValueError):
            verify_certificate(changed)

    def test_identity_target(self):
        instance = toy(13, 0)
        solved = solve_hashed(instance)
        self.assertEqual(solved["scalar"], "0")
        self.assertEqual(verify_certificate(solved)["status"], "verified")

    def test_bsgs_interval_boundaries(self):
        for secret in (0, 1, 45, 46, 2002):
            instance = toy(13, secret)
            solved = bsgs(instance, instance.order, 1000, 5)
            self.assertEqual(int(solved["scalar"]), secret)
        instance = toy(13, 1427)
        self.assertEqual(bsgs(instance, 1427, 1000, 5)["status"], "not_found_in_interval")
        self.assertEqual(bsgs(instance, 1428, 1000, 5)["scalar"], "1427")

    def test_rho_solves_small_target_and_resumes(self):
        instance = toy(13, 1427)
        with tempfile.TemporaryDirectory() as folder:
            checkpoint = Path(folder) / "rho.json"
            first = rho(instance, 3, 5, 7, checkpoint)
            self.assertEqual(first["status"], "budget_exhausted")
            self.assertTrue(checkpoint.exists())
            solved = rho(instance, 10000, 5, 7, checkpoint)
            self.assertEqual(solved["scalar"], "1427")
            with self.assertRaises(ValueError):
                rho(replace(instance, Q=instance.P), 100, 5, 7, checkpoint)
            changed = json.loads(checkpoint.read_text())
            changed["tortoise"]["a"] = str(int(changed["tortoise"]["a"]) + 1)
            checkpoint.write_text(json.dumps(changed))
            with self.assertRaises(ValueError):
                rho(instance, 100, 5, 7, checkpoint)

    def test_challenge_preflight_and_zero_budget(self):
        with self.assertRaises(BudgetExceeded):
            solve_hashed(challenge())
        with self.assertRaises(BudgetExceeded):
            solve_hashed(toy(13), seconds=0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
