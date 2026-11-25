"""Replay the emitted DIMACS and check a full auxiliary assignment.

The exhaustive 18-bit selector semantics are checked independently by the
Rust compact_chord_equivalence test. These tests check the gate emitter and
DIMACS serialization; they are not an SP screen.
"""

import hashlib
import importlib.util
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
CRATE = HERE.parent
SPEC = importlib.util.spec_from_file_location("m3_compact_cnf", CRATE / "tools/m3_compact_cnf.py")
MOD = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MOD)
FIXTURES = CRATE / "fixtures/s5"
HASHES = {
    "lead2b-s5-planted.ir": "1dd4ef93b48499871e822f38e693f7d4d18a8c5cf4942e9345d3d866f8705a36",
    "lead2b-s5-natural.ir": "701972399e5849cabebcb35df5538990e335038e32a068a9185cdb89e7f45216",
    "lead2b-s5-exact-unsat.ir": "53fa0069d6b5a4f5bee30f001904d31b7d96f05c76e6da3834fc29a935d1552f",
}


def group_add(a, b, p, curve_a):
    if a is None:
        return b
    if b is None:
        return a
    x, y = a
    v, w = b
    if x == v and (y + w) % p == 0:
        return None
    if a == b:
        slope = ((3 * x * x + curve_a) * pow(2 * y, -1, p)) % p
    else:
        slope = ((w - y) * pow((v - x) % p, -1, p)) % p
    out_x = (slope * slope - x - v) % p
    return out_x, (slope * (x - out_x) - y) % p


def planted_selector(data):
    p, target, windows = MOD.parse_ir(data)
    fields = dict(line.split("=", 1) for line in data.decode().splitlines()[1:])
    curve_a = int(fields["a"])
    lookup = {point: slot for slot, point in enumerate(windows[2])}
    found = []
    for i, first in enumerate(windows[0]):
        for j, second in enumerate(windows[1]):
            sum_pair = group_add(first, second, p, curve_a)
            neg_sum = None if sum_pair is None else (sum_pair[0], (-sum_pair[1]) % p)
            needed = group_add(target, neg_sum, p, curve_a)
            if needed in lookup:
                found.append((i, j, lookup[needed]))
    assert len(found) == 1
    bits = 0
    for w, slot in enumerate(found[0]):
        index, sign = divmod(slot, 2)
        bits |= index << (5 * w)
        bits |= sign << (15 + w)
    return bits


def read_dimacs(path, values):
    metadata, nvars, expected_clauses, seen = {}, None, None, 0
    bad = 0
    with path.open(encoding="ascii") as stream:
        for line in stream:
            if line.startswith("c "):
                if "=" in line:
                    key, value = line[2:].strip().split("=", 1)
                    metadata[key] = value
                continue
            if line.startswith("p "):
                _, fmt, var_word, clause_word = line.split()
                assert fmt == "cnf"
                nvars, expected_clauses = int(var_word), int(clause_word)
                continue
            words = [int(word) for word in line.split()]
            assert words and words[-1] == 0
            clause = words[:-1]
            assert all(1 <= abs(lit) <= nvars for lit in clause)
            seen += 1
            if not any(values[abs(lit)] == (lit > 0) for lit in clause):
                bad += 1
    assert seen == expected_clauses and nvars == len(values)
    return metadata, nvars, seen, bad


class CompactCnfTest(unittest.TestCase):
    def test_primitive_gate_truth_tables(self):
        for inputs in range(8):
            with self.subTest(inputs=inputs):
                c = MOD.Circuit(inputs)
                a, b, s = 1, 2, 3
                outputs = [c.and_(a, b), c.xor(a, b), c.mux(s, a, b)]
                expected = [
                    c.val(a) and c.val(b),
                    c.val(a) != c.val(b),
                    c.val(b) if c.val(s) else c.val(a),
                ]
                self.assertEqual([c.val(lit) for lit in outputs], expected)
                self.assertTrue(all(any(c.val(lit) for lit in clause) for clause in c.clauses))
                for output in outputs:
                    if abs(output) == MOD.TRUE:
                        continue
                    altered = dict(c.values)
                    altered[abs(output)] = not altered[abs(output)]
                    self.assertTrue(any(
                        not any(altered[abs(lit)] == (lit > 0) for lit in clause)
                        for clause in c.clauses
                    ))

    def test_modular_constraints_exhaustive_small_prime(self):
        p = 5
        for a in range(p):
            for b in range(p):
                for op, expected in (
                    ("mod_add", (a + b) % p),
                    ("mod_sub", (a - b) % p),
                    ("mod_mul", (a * b) % p),
                ):
                    with self.subTest(a=a, b=b, op=op):
                        c = MOD.Circuit()
                        x, y = c.variable_word(a), c.variable_word(b)
                        out = getattr(c, op)(x, y, p)
                        self.assertEqual(c.value(out), expected)
                        self.assertTrue(all(any(c.val(lit) for lit in clause) for clause in c.clauses))
                        altered = dict(c.values)
                        altered[abs(out[0])] = not altered[abs(out[0])]
                        self.assertTrue(any(
                            not any(altered[abs(lit)] == (lit > 0) for lit in clause)
                            for clause in c.clauses
                        ))

    def test_planted_model_and_rejected_selector(self):
        data = (FIXTURES / "lead2b-s5-planted.ir").read_bytes()
        self.assertEqual(hashlib.sha256(data).hexdigest(), HASHES["lead2b-s5-planted.ir"])
        selected = planted_selector(data)
        self.assertEqual(selected, 0x2EDDF)  # indices (31,14,27), signs (1,0,1)
        circuit = MOD.build(data, selected)
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "compact.cnf"
            MOD.write_dimacs(circuit, data, path)
            metadata, nvars, nclauses, bad = read_dimacs(path, circuit.values)
            self.assertEqual(metadata["canonical_ir_sha256"], hashlib.sha256(data).hexdigest())
            self.assertEqual((nvars, nclauses), (circuit.next_var - 1, len(circuit.clauses)))
            self.assertEqual(bad, 0)
            with self.assertRaises(FileExistsError):
                MOD.write_dimacs(circuit, data, path)
        rejected = MOD.build(data, selected ^ 1)
        self.assertEqual(rejected.clauses, circuit.clauses)
        self.assertGreater(sum(not any(rejected.val(lit) for lit in clause)
                               for clause in rejected.clauses), 0)

    def test_null_controls_have_rejected_sample(self):
        for name in ("lead2b-s5-natural.ir", "lead2b-s5-exact-unsat.ir"):
            with self.subTest(name=name):
                data = (FIXTURES / name).read_bytes()
                self.assertEqual(hashlib.sha256(data).hexdigest(), HASHES[name])
                circuit = MOD.build(data, 0)
                with tempfile.TemporaryDirectory() as folder:
                    path = Path(folder) / "compact.cnf"
                    MOD.write_dimacs(circuit, data, path)
                    metadata, _, _, bad = read_dimacs(path, circuit.values)
                    self.assertEqual(metadata["canonical_ir_sha256"], hashlib.sha256(data).hexdigest())
                    self.assertGreater(bad, 0)


if __name__ == "__main__":
    unittest.main()
