"""Four free product-code axes in a 128-dimensional N41 root quotient."""
import hashlib
import importlib.util
import json
import itertools
import resource
import signal
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
CFG = json.loads((HERE / "protocol.json").read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


for name, item in CFG["sources"].items():
    assert sha(item["path"]) == item["sha256"], name
assert CFG["status"] == "FROZEN_N41_FOUR_CODE_SUFFIX_QUOTIENT"
assert not (HERE / "result.json").exists()
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
target_table = json.loads(Path(CFG["sources"]["target_table"]["path"]).read_text())
assert len(terms) == 170 and len(cases) == 1554
assert target_table["status"] == "PASS_N41_FOURTH_PAIR_TARGET_TABLE"
assert target_table["rows"][0][0]["chart"] == 112961062585


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


class CodeRing2:
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


class CodeRing3:
    """Adjoin r with (r+r0)(r+r1)=0 to the existing p,q code ring."""

    def __init__(self, base, rvals):
        self.base = base
        self.rvals = tuple(rvals)
        assert len(set(rvals)) == 2
        self.sr = rvals[0] ^ rvals[1]
        self.pr = mul(rvals[0], rvals[1])
        self.zero = (base.zero, base.zero)
        self.one = (base.one, base.zero)
        self.p = (base.p, base.zero)
        self.q = (base.q, base.zero)
        self.r = (base.zero, base.one)
        self.mul_calls = 0

    def add(self, a, b):
        return (self.base.add(a[0], b[0]), self.base.add(a[1], b[1]))

    def scalar(self, a, value):
        return (self.base.scalar(a[0], value), self.base.scalar(a[1], value))

    def times(self, a, b):
        self.mul_calls += 1
        ac = self.base.times(a[0], b[0])
        bd = self.base.times(a[1], b[1])
        ad = self.base.times(a[0], b[1])
        bc = self.base.times(a[1], b[0])
        return (self.base.add(ac, self.base.scalar(bd, self.pr)),
                self.base.add(self.base.add(ad, bc), self.base.scalar(bd, self.sr)))

    def sq(self, a):
        aa, bb = self.base.sq(a[0]), self.base.sq(a[1])
        return (self.base.add(aa, self.base.scalar(bb, self.pr)),
                self.base.scalar(bb, self.sr))

    def power(self, a, exponent):
        value = self.one
        for _ in range(exponent):
            value = self.times(value, a)
        return value

    def inverse(self, a):
        aa = self.base.sq(a[0])
        ab = self.base.times(a[0], a[1])
        bb = self.base.sq(a[1])
        norm = self.base.add(aa, self.base.add(
            self.base.scalar(ab, self.sr), self.base.scalar(bb, self.pr)))
        invnorm = self.base.inverse(norm)
        numerator0 = self.base.add(a[0], self.base.scalar(a[1], self.sr))
        value = (self.base.times(numerator0, invnorm),
                 self.base.times(a[1], invnorm))
        assert self.times(a, value) == self.one
        return value


class CodeRing4(CodeRing3):
    """Adjoin fourth product code w with two exact field values."""

    def __init__(self, base, wvals):
        super().__init__(base, wvals)
        self.w = self.r
        self.r = (base.r, base.zero)


class RootRing:
    """R[U]/H with monic degree-eight H and 128 field coordinates."""

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


def upper_norm(root_ring, target, third_seed):
    """Q(U,r,t) after eliminating the third pair's quadratic root."""
    k = root_ring
    one = k.one
    u = k.u
    t = target
    r = (k.r.r,) + tuple([k.r.zero] * 7)
    u_plus = k.add(u, one)
    t_plus = k.add(t, one)
    up = k.times(u, u_plus)
    tp = k.times(t, t_plus)
    a = k.add(k.add(k.sq(t), k.times(up, tp)), k.sq(t_plus))
    b = k.times(up, tp)
    d = k.add(k.times(k.sq(u_plus), k.sq(t)),
              k.times(k.sq(u), k.sq(t_plus)))
    ss = square(third_seed)
    l = k.add(one, r)
    m = k.add(k.times(l, b), k.times(r, a))
    n = k.add(k.times(l, d), k.scalar(a, ss))
    return k.add(k.add(k.times(l, k.sq(n)),
                       k.times(r, k.times(n, m))),
                 k.scalar(k.sq(m), ss))


def zero_fingerprint(root_ring, norm_value, checkpoints):
    powers = [norm_value]
    for _ in range(40):
        powers.append(root_ring.sq(powers[-1]))
    indicator = root_ring.one
    rows = []
    evaluated = 0
    for index in range(max(checkpoints)):
        coefficient = DUAL[index]
        bit = root_ring.zero
        for power in powers:
            bit = root_ring.add(bit, root_ring.scalar(power, coefficient))
            coefficient = square(coefficient)
        assert root_ring.sq(bit) == bit
        factor = root_ring.add(root_ring.one, bit)
        indicator = root_ring.times(indicator, factor)
        evaluated += 1
        if evaluated in checkpoints:
            assert root_ring.sq(indicator) == indicator
            rows.append({"bits": evaluated, "nonzero": indicator != root_ring.zero,
                         "residue": indicator})
        if indicator == root_ring.zero:
            break
    for count in checkpoints:
        if count > evaluated:
            rows.append({"bits": count, "nonzero": False,
                         "residue": root_ring.zero})
    assert [row["bits"] for row in rows] == checkpoints
    return rows, evaluated


blocks = geo["blocks"]
permitted = geo["permitted_canonical_a"]
checkpoints = CFG["checkpoints"]
assert checkpoints == [8, 12, 16, 24]
rows = []
suffix_columns = set()
for axis, state in enumerate(CFG["suffix_state_ids"], 4):
    suffix_columns.update(blocks[axis]["states"][state]["columns"])
assert len(suffix_columns) == 6


def target_element(root_ring, wvals, chart_values):
    """Unique affine interpolation across the two fourth-code values."""
    assert len(chart_values) == 2 and wvals[0] != wvals[1]
    slope = mul(chart_values[0] ^ chart_values[1], F.inv(wvals[0] ^ wvals[1]))
    intercept = chart_values[0] ^ mul(slope, wvals[0])
    value = root_ring.r.add(root_ring.r.scalar(root_ring.r.one, intercept),
                            root_ring.r.scalar(root_ring.r.w, slope))
    return (value,) + tuple([root_ring.r.zero] * 7)


for panel in CFG["boxes"]:
    quads = [tuple(x) for x in panel["code_quads"]]
    code_lists = [sorted({quad[axis] for quad in quads}) for axis in range(4)]
    assert all(len(codes) == 2 for codes in code_lists)
    assert set(quads) == set(itertools.product(*code_lists))
    for quad in quads:
        columns = [set(blocks[axis]["states"][4*code]["columns"])
                   for axis, code in enumerate(quad)]
        assert all(not columns[axis] & suffix_columns for axis in range(4))
        assert all(not columns[i] & columns[j] for i in range(4) for j in range(i+1, 4))
    assert all([permitted[code] >> 2 for code in code_lists[axis]] ==
               [panel["prefix"][axis]] * 2 for axis in range(4))
    pvals = [product(blocks[0], permitted[code]) for code in code_lists[0]]
    qvals = [product(blocks[1], permitted[code]) for code in code_lists[1]]
    rvals = [product(blocks[2], permitted[code]) for code in code_lists[2]]
    wvals = [product(blocks[3], permitted[code]) for code in code_lists[3]]
    tick = time.monotonic()
    base = CodeRing2(pvals, qvals)
    middle = CodeRing3(base, rvals)
    region = CodeRing4(middle, wvals)
    h = h_in_region(region, blocks)
    h_seconds = time.monotonic() - tick
    tick = time.monotonic()
    k = RootRing(region, h)
    target_charts = [[target_table["rows"][code][state]["chart"]
                      for code in code_lists[3]] for state in range(4)]
    norms = [upper_norm(k, target_element(k, wvals, values), blocks[2]["s"])
             for values in target_charts]
    norm_value = k.one
    for norm in norms:
        norm_value = k.times(norm_value, norm)
    norm_seconds = time.monotonic() - tick
    tick = time.monotonic()
    checks, evaluated = zero_fingerprint(k, norm_value, checkpoints)
    feature_seconds = time.monotonic() - tick
    rejected = not checks[-1]["nonzero"]
    if [24, 37, 10, 0] in panel["code_quads"]:
        assert not rejected
    rows.append({"label": panel["label"], "prefix": panel["prefix"],
                 "code_quads": panel["code_quads"],
                 "code_lists": code_lists,
                 "p_values": pvals, "q_values": qvals, "r_values": rvals,
                 "w_values": wvals, "target_charts": target_charts,
                 "h": h, "upper_norm": norm_value,
                 "fingerprint_checks": checks,
                 "bits_evaluated": evaluated,
                 "target_rejected": rejected,
                 "code_ring_mul_calls": region.mul_calls,
                 "middle_ring_mul_calls": middle.mul_calls,
                 "base_ring_mul_calls": base.mul_calls,
                 "phase_seconds": {"symbolic_h": h_seconds,
                                   "upper_norm": norm_seconds,
                                   "zero_fingerprint": feature_seconds}})
    assert resource.getrusage(resource.RUSAGE_SELF).ru_maxrss < CFG["rss_cap_bytes"]

result = {"status": "PASS_N41_FOUR_CODE_SUFFIX_QUOTIENT",
          "candidate_id": None, "curve_id": CFG["curve_id"],
          "boxes": len(rows), "families_covered": sum(len(row["code_quads"]) for row in rows),
          "checkpoints": checkpoints,
          "rejected_by_checkpoint": {str(count): sum(not row["fingerprint_checks"][i]["nonzero"]
                                                for row in rows)
                                     for i, count in enumerate(checkpoints)},
          "rejected_boxes": sum(row["target_rejected"] for row in rows),
          "setup_seconds": setup_seconds, "wall_seconds": time.monotonic() - started,
          "self_maxrss_raw": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
          "rows": rows, "protocol_sha256": sha(HERE / "protocol.json")}
(HERE / "result.json").write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
signal.alarm(0)
print(json.dumps({"status": result["status"], "wall_seconds": result["wall_seconds"],
                  "rejected_boxes": result["rejected_boxes"],
                  "code_mul_calls": sum(row["code_ring_mul_calls"] for row in rows)},
                 sort_keys=True))
