"""Exact x-affine rank of widened three-pair code families over N41/N131."""
import hashlib
import json
import resource
import signal
import time
from pathlib import Path

from sage.all import EllipticCurve, GF, PolynomialRing

HERE = Path(__file__).resolve().parent
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
cfg = json.loads((HERE / "protocol_v2.json").read_text())
assert cfg["status"] == "FROZEN_BEFORE_TRIPLE_X_PREFIX_CAPACITY_V2"
for name, item in cfg["sources"].items():
    assert sha(item["path"]) == item["sha256"], name
signal.alarm(cfg["wall_cap_seconds"])
started = time.monotonic()


def make_curve(n):
    R = PolynomialRing(GF(2), "t")
    t = R.gen()
    modulus = t**41 + t**3 + 1 if n == 41 else t**131 + t**13 + t**2 + t + 1
    F = GF(2**n, name="t", modulus=modulus)
    E = EllipticCurve(F, [1, 0, 0, 0, 1])
    def dec(value):
        return F(R([(int(value) >> i) & 1 for i in range(n)]))
    def enc(value):
        return sum(int(bit) << i for i, bit in enumerate(value.polynomial().list()))
    def point(row):
        return E(dec(row[0]), dec(row[1]))
    return F, E, dec, enc, point


def rank(values):
    base = values[0]
    pivots = {}
    for value in values[1:]:
        word = value ^ base
        while word:
            bit = word.bit_length() - 1
            if bit in pivots:
                word ^= pivots[bit]
            else:
                pivots[bit] = word
                break
    return base, pivots


def contains(base, pivots, value):
    word = value ^ base
    while word:
        bit = word.bit_length() - 1
        if bit not in pivots:
            return False
        word ^= pivots[bit]
    return True


def triple_x(E, enc, first, second, third):
    values = set()
    for a in first:
        for b in second:
            ab = a + b
            for c in third:
                total = ab + c
                assert total != E(0)
                values.add(enc(total[0]))
    assert len(values) == 32
    return sorted(values)


def summarize(n, E, enc, first_families, fixed1, fixed2, residuals):
    grouped, rows = [], []
    values = set()
    for index, family in enumerate(first_families, 1):
        local = triple_x(E, enc, family, fixed1, fixed2)
        grouped.append(local)
        values.update(local)
        base, pivots = rank(sorted(values))
        rows.append({"first_family_count": index,
                     "distinct_x": len(values),
                     "affine_rank": len(pivots),
                     "affine_codimension": n - len(pivots),
                     "target_checks": {name: {
                         "exact_x_member": x in values,
                         "affine_hull_contains": contains(base, pivots, x)}
                         for name, x in residuals.items()}})
    return grouped, rows


g41 = json.loads(Path(cfg["sources"]["n41_geometry"]["path"]).read_text())
r41 = json.loads(Path(cfg["sources"]["n41_relation"]["path"]).read_text())
assert r41["status"] == "PASS_INDEPENDENT_N41_PUBLIC_SIX_PAIR_RELATION"
F41, E41, dec41, enc41, point41 = make_curve(41)
blocks = g41["blocks"][:6]
fixed_masks = cfg["n41_fixed_masks"]
fixed41 = [[point41(s["raw_sum"]) for s in blocks[slot]["states"]
            if s["a"] == mask]
           for slot, mask in ((1, fixed_masks[0]), (2, fixed_masks[1]))]
assert all(len(f) == 4 for f in fixed41)
fixed_cols = {col for slot, mask in ((1, fixed_masks[0]), (2, fixed_masks[1]))
              for row in blocks[slot]["states"] if row["a"] == mask
              for col in row["columns"]}
masks41 = [217]
for mask in g41["permitted_canonical_a"]:
    if mask == 217:
        continue
    rows = [s for s in blocks[0]["states"] if s["a"] == mask]
    assert len(rows) == 4
    if not (set(rows[0]["columns"]) & fixed_cols):
        masks41.append(mask)
    if len(masks41) == 8:
        break
assert len(masks41) == 8
families41 = [[point41(s["raw_sum"]) for s in blocks[0]["states"]
               if s["a"] == mask] for mask in masks41]
target41 = point41(r41["raw_target_replayed"])
suffix41 = sum((point41(row["pair_rotated"])
                for row in r41["source_pairs"][3:6]), E41(0))
residual41 = target41 - suffix41
assert residual41 != E41(0)
x41 = {"constructed": enc41(residual41[0])}
grouped41, rows41 = summarize(41, E41, enc41, families41,
                             fixed41[0], fixed41[1], x41)
assert rows41[0]["target_checks"]["constructed"]["exact_x_member"]

panel = json.loads(Path(cfg["sources"]["n131_first_variants"]["path"]).read_text())
prior = json.loads(Path(cfg["sources"]["n131_sixpair_panel"]["path"]).read_text())["n131"]
public = json.loads(Path(cfg["sources"]["n131_public"]["path"]).read_text())
assert public["curve_id"] == cfg["curve_ids"][1]
F131, E131, dec131, enc131, point131 = make_curve(131)
fixed131 = [[point131(row) for root in prior["edges"][slot]["roots"] for row in root]
            for slot in cfg["n131_fixed_edges"]]
assert all(len(f) == 4 for f in fixed131)
variants = list(panel["variants"])
assert len(variants) == 4
seed = 898618


def halftrace(value):
    term, out = value, F131.zero()
    for _ in range(66):
        out += term
        term = term**4
    assert out**2 + out == value
    return out


def source(mask):
    w = dec131(mask << 1)
    assert w and w.trace() == 0 and (1 / w).trace() == 0
    x = 1 + 1 / halftrace(w)
    points = E131.lift_x(x, all=True)
    assert len(points) == 2
    return points[0]


def orbit_key(mask):
    point = 4 * source(mask)
    assert point != E131(0)
    x, smallest = point[0], None
    for _ in range(131):
        value = enc131(x)
        smallest = value if smallest is None else min(smallest, value)
        x = x**2
    return smallest


fixed_keys = {orbit_key(mask) for edge in prior["edges"][1:]
              for mask in edge["masks"]}
assert len(fixed_keys) == 10
fifth = None
for mask in range(47, 512):
    mate = mask ^ seed
    if any(mask in row["masks"] or mate in row["masks"] for row in variants):
        continue
    a, b = dec131(mask << 1), dec131(mate << 1)
    if not a or not b or a.trace() or b.trace():
        continue
    if (1/a).trace() or (1/b).trace():
        continue
    keys = [orbit_key(mask), orbit_key(mate)]
    if keys[0] == keys[1] or any(key in fixed_keys for key in keys):
        continue
    left, right = source(mask), source(mate)
    states = [p + q for p in (left, -left) for q in (right, -right)]
    assert all(p != E131(0) for p in states)
    groups = {}
    for p in states:
        groups.setdefault(enc131(p[0]), []).append(p)
    assert len(groups) == 2 and all(len(v) == 2 for v in groups.values())
    fifth = {"masks": [mask, mate], "columns": keys,
             "points": states}
    break
assert fifth is not None
families131 = [[point131(row) for root in item["roots"] for row in root]
               for item in variants] + [fifth["points"]]
constructed131 = sum((point131(edge["roots"][0][0])
                      for edge in prior["edges"]), E131(0))
panel_public131 = point131(panel["target"])
public131 = point131(public["raw_point"])
suffix131 = sum((point131(prior["edges"][slot]["roots"][0][0])
                 for slot in cfg["n131_fixed_suffix_edges"]), E131(0))
residuals131 = {"constructed": constructed131 - suffix131,
                "panel_public": panel_public131 - suffix131,
                "public": public131 - suffix131}
assert all(p != E131(0) for p in residuals131.values())
x131 = {name: enc131(point[0]) for name, point in residuals131.items()}
grouped131, rows131 = summarize(131, E131, enc131, families131,
                               fixed131[0], fixed131[1], x131)
assert rows131[0]["target_checks"]["constructed"]["exact_x_member"]

payload = {"n41": grouped41, "n131": grouped131}
sets_path = HERE / "x_sets_v2.json"
assert not sets_path.exists()
sets_path.write_text(json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n")
result = {"status": "PASS_TRIPLE_X_PREFIX_CAPACITY",
          "candidate_id": None, "curve_ids": cfg["curve_ids"],
          "n41": {"first_masks": masks41, "fixed_masks": fixed_masks,
                  "residual_x": x41, "rows": rows41},
          "n131": {"first_masks": [item["masks"] for item in variants]
                   + [fifth["masks"]],
                   "fifth_columns": fifth["columns"],
                   "fixed_edges": cfg["n131_fixed_edges"],
                   "residual_x": x131, "rows": rows131},
          "x_sets_sha256": sha(sets_path),
          "wall_seconds": time.monotonic() - started,
          "self_maxrss_raw": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
          "protocol_sha256": sha(HERE / "protocol_v2.json")}
(HERE / "result_v2.json").write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
signal.alarm(0)
print(json.dumps({"status": result["status"], "wall_seconds": result["wall_seconds"],
                  "n41_ranks": [row["affine_rank"] for row in rows41],
                  "n131_ranks": [row["affine_rank"] for row in rows131]}, sort_keys=True))
