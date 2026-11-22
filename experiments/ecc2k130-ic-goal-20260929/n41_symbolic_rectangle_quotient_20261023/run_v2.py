"""Unspecialized 2x2 product-code quotient over GF(2^41), one cubic bit."""
import hashlib
import importlib.util
import json
import resource
import signal
import struct
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
CFG = json.loads((HERE / "protocol_v2.json").read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


for name, item in CFG["sources"].items():
    assert sha(item["path"]) == item["sha256"], name
assert CFG["status"] == "FROZEN_N41_COMPLETE_2X2_SWEEP"
assert not (HERE / "result_v2.json").exists()
signal.alarm(CFG["wall_cap_seconds"])
started = time.monotonic()
spec = importlib.util.spec_from_file_location("source_field", CFG["sources"]["field_arithmetic"]["path"])
source = importlib.util.module_from_spec(spec)
spec.loader.exec_module(source)
F = source.Field(41, [0, 3])
mul = F.mul
square = lambda x: mul(x, x)
geo = json.loads(Path(CFG["sources"]["geometry"]["path"]).read_text())
terms = json.loads(Path(CFG["sources"]["root_polynomial"]["path"]).read_text())["terms"]
cases = [json.loads(line) for line in Path(CFG["sources"]["coordinate_audit"]["path"]).open()]
target_x = struct.unpack("<65Q", Path(CFG["sources"]["target_residuals"]["path"]).read_bytes())[0]
assert len(terms) == 170 and len(cases) == 1554


def trace(x):
    acc = x
    for _ in range(40):
        x = square(x)
        acc ^= x
    assert acc in (0, 1)
    return acc


def dual_basis():
    powers = [1]
    for _ in range(80):
        powers.append(mul(powers[-1], 2))
    t = [trace(x) for x in powers]
    rows = [sum(t[i + j] << j for j in range(41)) | (1 << (41 + i))
            for i in range(41)]
    for col in range(41):
        pivot = next(row for row in range(col, 41) if rows[row] >> col & 1)
        rows[col], rows[pivot] = rows[pivot], rows[col]
        for row in range(41):
            if row != col and rows[row] >> col & 1:
                rows[row] ^= rows[col]
    assert [row & ((1 << 41) - 1) for row in rows] == [1 << i for i in range(41)]
    return [sum((rows[j] >> (41 + i) & 1) << j for j in range(41))
            for i in range(41)]


DUAL = dual_basis()
setup_seconds = time.monotonic() - started


def product(block, mask):
    value = 0
    for i, basis in enumerate(block["product_basis"]):
        if mask >> i & 1:
            value ^= basis
    return value


class CodeRing:
    """F[p,q]/((p+p0)(p+p1),(q+q0)(q+q1)), basis 1,p,q,pq."""

    zero = (0, 0, 0, 0)
    one = (1, 0, 0, 0)
    p = (0, 1, 0, 0)
    q = (0, 0, 1, 0)

    def __init__(self, pvals, qvals):
        self.pvals, self.qvals = tuple(pvals), tuple(qvals)
        assert len(set(pvals)) == len(set(qvals)) == 2
        self.p_reduce = {0: ((0, 1),), 1: ((1, 1),),
                         2: ((0, mul(pvals[0], pvals[1])),
                             (1, pvals[0] ^ pvals[1]))}
        self.q_reduce = {0: ((0, 1),), 1: ((1, 1),),
                         2: ((0, mul(qvals[0], qvals[1])),
                             (1, qvals[0] ^ qvals[1]))}
        self.table = {}
        for i in range(4):
            for j in range(4):
                self.table[i, j] = tuple(
                    (pa + 2 * qa, mul(pc, qc))
                    for pa, pc in self.p_reduce[(i & 1) + (j & 1)]
                    for qa, qc in self.q_reduce[(i >> 1) + (j >> 1)])
        self.mul_calls = 0

    @staticmethod
    def add(a, b):
        return tuple(x ^ y for x, y in zip(a, b))

    @staticmethod
    def scalar(a, value):
        return tuple(mul(x, value) for x in a)

    def times(self, a, b):
        self.mul_calls += 1
        out = [0] * 4
        for i, x in enumerate(a):
            if x:
                for j, y in enumerate(b):
                    if y:
                        coefficient = mul(x, y)
                        for k, factor in self.table[i, j]:
                            if factor:
                                out[k] ^= mul(coefficient, factor)
        return tuple(out)

    def sq(self, a):
        out = [0] * 4
        for i, x in enumerate(a):
            if x:
                coefficient = square(x)
                for k, factor in self.table[i, i]:
                    if factor:
                        out[k] ^= mul(coefficient, factor)
        return tuple(out)

    def power(self, a, exponent):
        result = self.one
        for _ in range(exponent):
            result = self.times(result, a)
        return result

    def inverse(self, a):
        cols = [self.times(a, tuple(int(i == j) for i in range(4)))
                for j in range(4)]
        rows = [[cols[j][i] for j in range(4)] + [int(i == j) for j in range(4)]
                for i in range(4)]
        for col in range(4):
            pivot = next(i for i in range(col, 4) if rows[i][col])
            rows[col], rows[pivot] = rows[pivot], rows[col]
            scale = F.inv(rows[col][col])
            rows[col] = [mul(scale, x) for x in rows[col]]
            for i in range(4):
                if i != col and rows[i][col]:
                    coefficient = rows[i][col]
                    rows[i] = [x ^ mul(coefficient, y)
                               for x, y in zip(rows[i], rows[col])]
        assert [row[:4] for row in rows] == [[int(i == j) for j in range(4)]
                                                for i in range(4)]
        inverse = tuple(row[4] for row in rows)
        assert self.times(a, inverse) == self.one
        return inverse


class RootRing:
    """R[U]/H with monic degree-eight H and 32 field coordinates."""

    def __init__(self, code_ring, h):
        self.r = code_ring
        assert len(h) == 9 and h[8] == code_ring.one
        self.h = h
        self.zero = tuple([code_ring.zero] * 8)
        self.one = (code_ring.one,) + tuple([code_ring.zero] * 7)
        self.u = (code_ring.zero, code_ring.one) + tuple([code_ring.zero] * 6)

    def add(self, a, b):
        return tuple(self.r.add(x, y) for x, y in zip(a, b))

    def scalar(self, a, value):
        return tuple(self.r.scalar(x, value) for x in a)

    def reduce(self, coefficients):
        out = list(coefficients) + [self.r.zero] * max(0, 8 - len(coefficients))
        for k in range(len(out) - 1, 7, -1):
            if out[k] != self.r.zero:
                for j in range(8):
                    if self.h[j] != self.r.zero:
                        out[k - 8 + j] = self.r.add(
                            out[k - 8 + j], self.r.times(out[k], self.h[j]))
        return tuple(out[:8])

    def times(self, a, b):
        out = [self.r.zero] * 15
        for i, x in enumerate(a):
            if x != self.r.zero:
                for j, y in enumerate(b):
                    if y != self.r.zero:
                        out[i + j] = self.r.add(out[i + j], self.r.times(x, y))
        return self.reduce(out)

    def sq(self, a):
        out = [self.r.zero] * 15
        for i, x in enumerate(a):
            out[2 * i] = self.r.sq(x)
        return self.reduce(out)


def h_in_region(r, blocks):
    a, b = blocks[0]["s"], blocks[1]["s"]
    a_powers = [1]
    b_powers = [1]
    for _ in range(8):
        a_powers.append(mul(a_powers[-1], a))
        b_powers.append(mul(b_powers[-1], b))
    p_powers = [r.power(r.p, i) for i in range(5)]
    q_powers = [r.power(r.q, i) for i in range(5)]
    h = [r.zero] * 9
    for ea, eb, ep, eq, ez in terms:
        c = mul(a_powers[ea], b_powers[eb])
        term = r.scalar(r.times(p_powers[ep], q_powers[eq]), c)
        h[ez] = r.add(h[ez], term)
    lead_inv = r.inverse(h[8])
    h = [r.times(c, lead_inv) for c in h]
    assert h[8] == r.one
    return tuple(h)


def chart_z(root_ring):
    r, h = root_ring.r, root_ring.h
    h_at_one = r.zero
    for coefficient in h:
        h_at_one = r.add(h_at_one, coefficient)
    inv_h1 = r.inverse(h_at_one)
    quotient = [r.zero] * 8
    quotient[7] = r.one
    for i in range(7, 0, -1):
        quotient[i - 1] = r.add(h[i], quotient[i])
    assert quotient[0] == r.add(h[0], h_at_one)
    inv_up1 = tuple(r.times(c, inv_h1) for c in quotient)
    assert root_ring.times(root_ring.add(root_ring.one, root_ring.u), inv_up1) == root_ring.one
    return root_ring.times(root_ring.u, inv_up1)


def cubic_bit(root_ring, z):
    powers = [z]
    for _ in range(40):
        powers.append(root_ring.sq(powers[-1]))
    bit_residues = []
    for index in CFG["bit_indices"]:
        alpha = DUAL[index]
        coefficient = alpha
        bit = root_ring.zero
        for power in powers:
            bit = root_ring.add(bit, root_ring.scalar(power, coefficient))
            coefficient = square(coefficient)
        assert root_ring.sq(bit) == bit
        bit_residues.append(bit)
    return root_ring.times(root_ring.times(bit_residues[0], bit_residues[1]),
                           bit_residues[2])


blocks = geo["blocks"]
permitted = geo["permitted_canonical_a"]
target_z = F.inv(target_x)
target_bit = int(all(target_z >> i & 1 for i in CFG["bit_indices"]))
assert target_bit == 1
rows = []
for panel in CFG["rectangles"]:
    selected = [cases[index] for index in panel["case_indices"]]
    left_codes = sorted({case["left_code"] for case in selected})
    right_codes = sorted({case["right_code"] for case in selected})
    assert len(left_codes) == len(right_codes) == 2
    assert {(case["left_code"], case["right_code"]) for case in selected} == {
        (left, right) for left in left_codes for right in right_codes}
    assert [permitted[left] >> 2 for left in left_codes] == [panel["prefix"][0]] * 2
    assert [permitted[right] >> 2 for right in right_codes] == [panel["prefix"][1]] * 2
    pvals = [product(blocks[0], permitted[code]) for code in left_codes]
    qvals = [product(blocks[1], permitted[code]) for code in right_codes]
    tick = time.monotonic()
    region = CodeRing(pvals, qvals)
    h = h_in_region(region, blocks)
    h_seconds = time.monotonic() - tick
    tick = time.monotonic()
    k = RootRing(region, h)
    z = chart_z(k)
    chart_seconds = time.monotonic() - tick
    tick = time.monotonic()
    bit = cubic_bit(k, z)
    feature_seconds = time.monotonic() - tick
    value = 0 if bit == k.zero else 1 if bit == k.one else None
    if 966 in panel["case_indices"]:
        assert value is None or value == target_bit
    rows.append({"label": panel["label"], "prefix": panel["prefix"],
                 "case_indices": panel["case_indices"],
                 "left_codes": left_codes, "right_codes": right_codes,
                 "p_values": pvals, "q_values": qvals,
                 "h": h, "cubic_residue": bit,
                 "cubic_constant": value, "target_bit": target_bit,
                 "target_rejected": value is not None and value != target_bit,
                 "code_ring_mul_calls": region.mul_calls,
                 "phase_seconds": {"symbolic_h": h_seconds,
                                   "quotient_chart": chart_seconds,
                                   "trace_and_cubic": feature_seconds}})
    assert resource.getrusage(resource.RUSAGE_SELF).ru_maxrss < CFG["rss_cap_bytes"]

result = {"status": "PASS_N41_SYMBOLIC_COMPLETE_2X2_SWEEP",
          "candidate_id": None, "curve_id": CFG["curve_id"],
          "rectangles": len(rows), "families_covered": sum(len(row["case_indices"]) for row in rows),
          "target_residual_index": CFG["target_residual_index"],
          "target_z": target_z, "bit_indices": CFG["bit_indices"],
          "setup_seconds": setup_seconds, "wall_seconds": time.monotonic() - started,
          "self_maxrss_raw": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
          "rows": rows, "protocol_sha256": sha(HERE / "protocol_v2.json")}
(HERE / "result_v2.json").write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
signal.alarm(0)
print(json.dumps({"status": result["status"], "wall_seconds": result["wall_seconds"],
                  "code_mul_calls": [row["code_ring_mul_calls"] for row in rows]},
                 sort_keys=True))
