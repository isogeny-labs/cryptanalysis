"""Exact four-family N41 output-region XCNF with symbolic product labels."""

import hashlib
import json
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
N = 41
MOD = (1 << 41) | (1 << 3) | 1
MASK = (1 << 41) - 1


def field_mul(a, b):
    v = 0
    while b:
        if b & 1:
            v ^= a
        b >>= 1
        a <<= 1
        if a >> N:
            a ^= MOD
    return v


def square(a):
    return field_mul(a, a)


def halftrace(a):
    total = 0
    for _ in range(21):
        total ^= a
        a = square(square(a))
    return total


def trace(a):
    v = 0
    for _ in range(N):
        v ^= a
        a = square(a)
    assert v in (0, 1)
    return v


COORD = [(halftrace(square(1 << i)), trace(square(1 << i))) for i in range(N)]
SEED = [(halftrace(square(1 << (i + 1))), trace(square(1 << (i + 1))))
        for i in range(6)]


def family_basis(code):
    p = code << 2
    columns = [(v ^ field_mul(p, 1 << i), bit) for i, (v, bit) in enumerate(COORD)]
    columns += SEED + [(1, 0)]
    rows = [0] * 42
    for j, (value, bit) in enumerate(columns):
        for i in range(N):
            if value >> i & 1:
                rows[i] ^= 1 << j
        if bit:
            rows[N] ^= 1 << j
    pivots = [-1] * 48
    rank = 0
    for col in range(48):
        found = next((i for i in range(rank, 42) if rows[i] >> col & 1), None)
        if found is None:
            continue
        rows[rank], rows[found] = rows[found], rows[rank]
        for i in range(42):
            if i != rank and rows[i] >> col & 1:
                rows[i] ^= rows[rank]
        pivots[col] = rank
        rank += 1
    output = []
    for free in range(48):
        if pivots[free] >= 0:
            continue
        vector = 1 << free
        for col in range(48):
            if pivots[col] >= 0 and rows[pivots[col]] >> free & 1:
                vector ^= 1 << col
        assert vector & MASK
        output.append(vector & MASK)
    assert len(output) in (6, 7)
    return output


class Circuit:
    def __init__(self):
        self.next_var = 1
        self.clauses = []
        self.xors = []
        self.and_cache = {}
        self.xor_cache = {}
        self.and_defs = {}
        self.xor_defs = {}
        self.primary = []
        self.red = [self.reduce(1 << k) for k in range(81)]

    @staticmethod
    def reduce(value):
        while value.bit_length() > N:
            value ^= MOD << (value.bit_length() - N - 1)
        return value

    def variable(self):
        value = self.next_var
        self.next_var += 1
        self.primary.append(value)
        return value

    def and_(self, a, b):
        if a == 0 or b == 0:
            return 0
        if a == -1:
            return b
        if b == -1:
            return a
        if a == b:
            return a
        key = tuple(sorted((a, b)))
        if key in self.and_cache:
            return self.and_cache[key]
        wire = self.next_var
        self.next_var += 1
        self.clauses += [f"-{a} -{b} {wire} 0", f"{a} -{wire} 0", f"{b} -{wire} 0"]
        self.and_cache[key] = wire
        self.and_defs[wire] = key
        return wire

    def xor(self, inputs):
        parity = 0
        terms = Counter()
        for wire in inputs:
            if wire == -1:
                parity ^= 1
            elif wire:
                terms[wire] ^= 1
        values = tuple(sorted(wire for wire, bit in terms.items() if bit))
        if not values:
            return -1 if parity else 0
        if len(values) == 1 and not parity:
            return values[0]
        key = (values, parity)
        if key in self.xor_cache:
            return self.xor_cache[key]
        wire = self.next_var
        self.next_var += 1
        self.xors.append("x " + str(wire if parity else -wire) + " " +
                         " ".join(map(str, values)) + " 0")
        self.xor_cache[key] = wire
        self.xor_defs[wire] = key
        return wire

    def element(self, terms):
        buckets = [[] for _ in range(N)]
        for wire, value in terms:
            while value:
                low = value & -value
                buckets[low.bit_length() - 1].append(wire)
                value ^= low
        return [self.xor(bucket) for bucket in buckets]

    def field_square(self, words):
        return self.element((wire, self.red[2 * i]) for i, wire in enumerate(words))

    def field_mul(self, a, b):
        return self.element((self.and_(x, y), self.red[i + j])
                            for i, x in enumerate(a) for j, y in enumerate(b))

    def constant_mul(self, a, value):
        return self.element((wire, field_mul(value, 1 << i))
                            for i, wire in enumerate(a))

    def require_zero(self, words):
        for wire in words:
            if wire == -1:
                self.clauses.append("0")
            elif wire:
                self.clauses.append(f"-{wire} 0")

    def write(self, path):
        with path.open("x") as out:
            out.write(f"p cnf {self.next_var - 1} {len(self.clauses) + len(self.xors)}\n")
            out.write("\n".join(self.clauses + self.xors) + "\n")

    def evaluate(self, primary):
        values = {0: False, -1: True}
        for wire in range(1, self.next_var):
            if wire in self.and_defs:
                a, b = self.and_defs[wire]
                values[wire] = values[a] and values[b]
            elif wire in self.xor_defs:
                parts, parity = self.xor_defs[wire]
                values[wire] = bool(parity) ^ (sum(values[x] for x in parts) % 2 == 1)
            else:
                values[wire] = bool(primary.get(wire, False))
        for row in self.clauses:
            assert row != "0"
            assert any((values[abs(int(x))] if int(x) > 0 else not values[-int(x)])
                       for x in row.split()[:-1])
        for row in self.xors:
            assert sum((values[abs(int(x))] if int(x) > 0 else not values[-int(x)])
                       for x in row.split()[1:-1]) % 2 == 1


def region(circuit, region_index):
    labels = [circuit.variable(), circuit.variable()]
    coefficients = [circuit.variable() for _ in range(7)]
    output_terms = []
    family_sizes = []
    for k in range(4):
        selector = circuit.and_(circuit.xor((labels[0], -1 if not k & 1 else 0)),
                                circuit.xor((labels[1], -1 if not k & 2 else 0)))
        basis = family_basis(4 * region_index + k)
        family_sizes.append(len(basis))
        for i, value in enumerate(basis):
            output_terms.append((circuit.and_(selector, coefficients[i]), value))
    output = circuit.element(output_terms)
    circuit.clauses.append(" ".join(str(v) for v in output if v > 0) + " 0")
    return output, labels, coefficients, family_sizes


def solve_coefficients(basis, value):
    pivots = {}
    for i, column in enumerate(basis):
        word, mask = column, 1 << i
        while word:
            bit = word.bit_length() - 1
            if bit in pivots:
                word ^= pivots[bit][0]
                mask ^= pivots[bit][1]
            else:
                pivots[bit] = (word, mask)
                break
    mask = 0
    while value:
        bit = value.bit_length() - 1
        assert bit in pivots
        value ^= pivots[bit][0]
        mask ^= pivots[bit][1]
    return mask


def build(name, left_region, right_region, target, positive=None):
    circuit = Circuit()
    c, cl, ca, ldim = region(circuit, left_region)
    d, dl, da, rdim = region(circuit, right_region)
    product = circuit.field_mul(c, d)
    z = circuit.constant_mul(product, target)
    total = circuit.element([(wire, 1 << i) for words in (c, d)
                             for i, wire in enumerate(words)] +
                            [(-1, target)])
    equation = [circuit.xor((x, y, w)) for x, y, w in
                zip(circuit.field_square(z), z, circuit.field_square(total))]
    circuit.require_zero(equation)
    if positive:
        assignment = {}
        for code, value, region_index, labels, coeffs in (
                (positive[0], positive[2], left_region, cl, ca),
                (positive[1], positive[3], right_region, dl, da)):
            assert code >> 2 == region_index
            bits = code & 3
            mask = solve_coefficients(family_basis(code), value)
            for i, wire in enumerate(labels):
                assignment[wire] = bits >> i & 1
            for i, wire in enumerate(coeffs):
                assignment[wire] = mask >> i & 1
        circuit.evaluate(assignment)
    path = HERE / f"{name}.xcnf"
    circuit.write(path)
    return {"name": name, "left_region": left_region, "right_region": right_region,
            "target_reciprocal": target, "left_family_dimensions": ldim,
            "right_family_dimensions": rdim, "symbolic_label_bits": 4,
            "primary_variables": len(circuit.primary),
            "variables": circuit.next_var - 1, "cnf_clauses": len(circuit.clauses),
            "xor_rows": len(circuit.xors), "and_gates": len(circuit.and_defs),
            "constructed_assignment_checked": bool(positive),
            "formula_sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


if __name__ == "__main__":
    result = [build("constructed_positive", 819 >> 2, 176 >> 2, 1515824644274,
                    (819, 176, 940337512568, 1570560155378)),
              build("public_same_regions", 819 >> 2, 176 >> 2, 1000731834126)]
    with (HERE / "build_result.json").open("x") as stream:
        json.dump({"status": "FORMULAS_BUILT", "cases": result}, stream, indent=2,
                  sort_keys=True)
        stream.write("\n")
