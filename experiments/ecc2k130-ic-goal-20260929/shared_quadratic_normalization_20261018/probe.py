"""Exact shared-quadratic and exceptional-code audit for frozen resultants."""
import hashlib
import json
from functools import reduce
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SOURCES = [
    ROOT / "n41_w11_freecode_resultant_20261018" / "resultant_input.tsv",
    ROOT / "n131_w33_freecode_resultant_20261018" / "coefficients.json",
]


class Field:
    def __init__(self, n, reduction):
        self.n, self.reduction, self.mask = n, reduction, (1 << n) - 1

    def mul(self, a, b):
        out = 0
        while b:
            if b & 1:
                out ^= a
            b >>= 1
            a <<= 1
            if a >> self.n:
                a = (a & self.mask) ^ self.reduction
        return out

    def square(self, a):
        return self.mul(a, a)

    def frob(self, a, k):
        for _ in range(k):
            a = self.square(a)
        return a

    def inv(self, a):
        assert a
        # In GF(2^n), a^(2^n-2) is the reciprocal.
        exponent = (1 << self.n) - 2
        out = 1
        while exponent:
            if exponent & 1:
                out = self.mul(out, a)
            a = self.square(a)
            exponent >>= 1
        return out


def rank_and_membership(basis, query):
    pivots = {}
    for value in basis:
        while value:
            bit = value.bit_length() - 1
            if bit not in pivots:
                pivots[bit] = value
                break
            value ^= pivots[bit]
    remainder = query
    while remainder:
        bit = remainder.bit_length() - 1
        if bit not in pivots:
            break
        remainder ^= pivots[bit]
    return len(pivots), remainder == 0, remainder


def input_rows():
    lines = SOURCES[0].read_text().splitlines()
    assert lines[0] == "FREECODE 25 281 13"
    n41 = []
    for index in (0, 1):
        offset = 1 + 281 + 14 * index
        target = list(map(int, lines[offset].split()[1:]))
        assert target[0] == index
        terms = {}
        for line in lines[offset + 1:offset + 14]:
            tag, row, i, j, c = line.split()
            assert tag == "C" and int(row) == index
            terms[(int(i), int(j))] = int(c)
        n41.append((target[1:], terms))
    data = json.loads(SOURCES[1].read_text())
    n131 = [(row["point"], {(i, j): c for i, j, c in row["terms"]})
            for row in data["rows"][:2]]
    return {41: n41, 131: n131}


def source_basis(field, seed, positions, rotation):
    return [field.frob(field.square(1 << (bit + 1)) ^
                       field.mul(seed, 1 << (bit + 1)), rotation)
            for bit in positions]


def source_value(code, basis):
    value = 0
    for i, b in enumerate(basis):
        if code >> i & 1:
            value ^= b
    return value


def evaluate(field, terms, p, q):
    pp, qq = [1, p], [1, q]
    for _ in range(3):
        pp.append(field.mul(pp[-1], p))
        qq.append(field.mul(qq[-1], q))
    return reduce(
        int.__xor__, (field.mul(c, field.mul(pp[i], qq[j]))
                      for (i, j), c in terms.items()), 0)


def leading_coefficient(field, c13, c33, p):
    return field.mul(c13, p) ^ field.mul(c33, field.mul(p, field.square(p)))


rows = input_rows()
out = {"status": "COMPLETE_SHARED_QUADRATIC_AUDIT", "candidate_id": None,
       "sources_sha256": {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                          for p in SOURCES}, "rows": []}
for n in (41, 131):
    field = Field(n, (1 << 3) | 1 if n == 41 else
                  (1 << 13) | (1 << 2) | (1 << 1) | 1)
    if n == 41:
        seed, positions, rotations = 112, [0, 1, 2, 3, 4, 6, 7, 8, 9, 10], (12, 24)
    else:
        seed_mask = 898618
        seed, positions, rotations = seed_mask << 1, [i for i in range(33)
            if i != seed_mask.bit_length() - 1], (0, 18)
    pb = source_basis(field, seed, positions, rotations[0])
    qb = source_basis(field, seed, positions, rotations[1])
    p_rank, zero_in_span, _ = rank_and_membership(pb, 0)
    q_rank, _, _ = rank_and_membership(qb, 0)
    assert p_rank == q_rank == len(positions) and zero_in_span
    pair_coeffs = [field.mul(field.square(qb[i]), qb[j]) ^
                   field.mul(qb[i], field.square(qb[j]))
                   for i in range(len(qb)) for j in range(i + 1, len(qb))]
    quad_rank, _, _ = rank_and_membership(pair_coeffs, 0)
    for target_index, (point, terms) in enumerate(rows[n]):
        assert sorted(terms) == [(0, 0), (0, 2), (0, 4), (1, 1), (1, 3),
                                 (2, 0), (2, 2), (2, 4), (3, 1), (3, 3),
                                 (4, 0), (4, 2), (4, 4)]
        c13, c33 = terms[(1, 3)], terms[(3, 3)]
        assert c13 and c33
        # A(p)=p(c13+c33*p^2): at most two roots in this field.
        other_root = field.frob(field.mul(c13, field.inv(c33)), n - 1)
        assert field.square(other_root) == field.mul(c13, field.inv(c33))
        assert other_root != 0
        root_rank, other_in_span, remainder = rank_and_membership(pb, other_root)
        assert root_rank == p_rank
        samples = [1, 2, 3, 7, (1 << len(pb)) - 1]
        checks = []
        for code in samples:
            p = source_value(code, pb)
            leading = leading_coefficient(field, c13, c33, p)
            if not leading:
                assert p == other_root
                continue
            inv_leading = field.inv(leading)
            assert field.mul(leading, inv_leading) == 1
            # The coefficient of each distinct y_i*y_j before division is A(p)*B_ij.
            for index in (0, 1, len(pair_coeffs) // 2, len(pair_coeffs) - 1):
                assert field.mul(inv_leading, field.mul(leading, pair_coeffs[index])) == pair_coeffs[index]
            for qcode in (0, 1, 3, 5, (1 << len(qb)) - 1):
                q = source_value(qcode, qb)
                value = evaluate(field, terms, p, q)
                assert (value == 0) == (field.mul(inv_leading, value) == 0)
            checks.append(code)
        if n == 41:
            exceptions = [code for code in range(1 << len(pb))
                          if leading_coefficient(field, c13, c33,
                                                 source_value(code, pb)) == 0]
            assert len(exceptions) == 1 + int(other_in_span)
        else:
            exceptions = None
        out["rows"].append({"field_degree": n, "target_index": target_index,
            "target_point": point, "source_bits": len(pb), "p_rank": p_rank,
            "q_rank": q_rank, "q_quadratic_coefficient_rank": quad_rank,
            "c13": c13, "c33": c33, "other_root": other_root,
            "other_root_in_source_span": other_in_span,
            "other_root_span_remainder": remainder,
            "exception_count": 1 + int(other_in_span),
            "exhaustive_n41_exception_codes": exceptions,
            "normalization_sample_codes_checked": checks})

(HERE / "result.json").write_text(json.dumps(out, sort_keys=True, indent=2) + "\n")
print(json.dumps({"status": out["status"], "rows": [
    {key: row[key] for key in ("field_degree", "target_index", "p_rank",
     "q_quadratic_coefficient_rank", "exception_count",
     "exhaustive_n41_exception_codes")}
    for row in out["rows"]]}, sort_keys=True))
