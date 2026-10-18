"""Quadratic Boolean evaluation ranks of frozen N41 three-code unions."""
import hashlib
import json
import resource
import time
from pathlib import Path

from sage.all import EllipticCurve, GF, PolynomialRing

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
protocol = json.loads((HERE / "protocol.json").read_text())
for relative, digest in protocol["sources_sha256"].items():
    assert hashlib.sha256((ROOT / relative).read_bytes()).hexdigest() == digest
assert protocol["worker_count"] == 1
assert json.loads((HERE / "sage_runtime_info.json").read_text())["status"] == "verified"

R = PolynomialRing(GF(2), "t")
t = R.gen()
field = GF(2**41, name="t", modulus=t**41 + t**3 + 1)
curve = EllipticCurve(field, [1, 0, 0, 0, 1])


def dec(value):
    return field(R([(value >> i) & 1 for i in range(41)]))


def enc(value):
    return sum(int(bit) << i for i, bit in enumerate(value.polynomial().list()))


def features(value):
    """1 constant, 41 linear, and 820 pair monomials in fixed order."""
    out = 1
    for i in range(41):
        if value >> i & 1:
            out |= 1 << (1 + i)
    column = 42
    for i in range(41):
        for j in range(i + 1, 41):
            if (value >> i & 1) and (value >> j & 1):
                out |= 1 << column
            column += 1
    assert column == 862
    return out


def insert(pivots, value):
    while value:
        k = value.bit_length() - 1
        if k not in pivots:
            pivots[k] = value
            return True
        value ^= pivots[k]
    return False


start = time.monotonic()
states = [[None] * 160 for _ in range(3)]
columns = [[None] * 40 for _ in range(3)]
input_file = ROOT / protocol["input"]
for line in input_file.read_text().splitlines():
    row = line.split()
    if row[0] != "S" or int(row[1]) >= 3:
        continue
    slot, sid = int(row[1]), int(row[2])
    states[slot][sid] = curve([dec(int(row[6])), dec(int(row[7]))])
    pair = (int(row[4]), int(row[5]))
    code = sid // 4
    if columns[slot][code] is None:
        columns[slot][code] = pair
    assert columns[slot][code] == pair
assert all(all(slot) for slot in states)

results = []
for a, b in protocol["pair_codes"]:
    union = set()
    pivots = {}
    rank_curve = []
    family_count = 0
    for c in range(40):
        used = (*columns[0][a], *columns[1][b], *columns[2][c])
        if len(set(used)) != 6:
            continue
        family_count += 1
        family = set()
        for i in range(2):
            for j in range(4):
                ab = states[0][4*a+i] + states[1][4*b+j]
                for k in range(4):
                    point = ab + states[2][4*c+k]
                    assert point != curve(0)
                    family.add(enc(point[0]))
        assert len(family) == 32
        assert not union.intersection(family)
        union.update(family)
        for x in sorted(family):
            insert(pivots, features(x))
        rank_curve.append([c, len(union), len(pivots)])
    assert len(union) == 32 * family_count
    result = {"codes": [a, b], "valid_third_codes": family_count,
              "distinct_union_x": len(union), "quadratic_rank": len(pivots),
              "quadratic_nullity": 862-len(pivots),
              "rank_after_each_third_code": rank_curve,
              "x_values": sorted(union)}
    results.append(result)
    print(json.dumps({k: result[k] for k in ("codes", "valid_third_codes",
          "distinct_union_x", "quadratic_rank", "quadratic_nullity")},
          sort_keys=True), flush=True)

wall = time.monotonic() - start
rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
assert wall < protocol["wall_cap_seconds"]
assert rss < protocol["rss_cap_bytes"]
out = {"status": "COMPLETE_N41_QUADRATIC_PAIR_UNION_PANEL",
       "candidate_id": None, "curve_id": "EC1N41Ckb1h7d5e80d3c4d0",
       "quadratic_monomials": 862, "results": results,
       "wall_seconds": wall, "peak_self_rss_bytes": rss,
       "protocol_sha256": hashlib.sha256((HERE / "protocol.json").read_bytes()).hexdigest()}
(HERE / "result.json").write_text(json.dumps(out, sort_keys=True, indent=2) + "\n")
