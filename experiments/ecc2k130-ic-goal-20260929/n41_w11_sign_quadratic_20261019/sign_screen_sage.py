"""Exact five-pair sign-quadratic determinant and full group-law audit."""
import hashlib
import itertools
import json
import resource
import time
from pathlib import Path
from sage.all import EllipticCurve, GF, PolynomialRing, matrix, vector

HERE = Path(__file__).resolve().parent
sha = lambda path: hashlib.sha256(Path(path).read_bytes()).hexdigest()
cfg = json.loads((HERE / "run_protocol.json").read_text())
assert cfg["status"] == "FROZEN_BEFORE_SIGN_SCREEN"
for label, source in cfg["sources"].items():
    assert sha(source["path"]) == source["sha256"], label
panel = json.loads((HERE / "panel.json").read_text())
assert panel["status"] == "FROZEN_SIGN_PANEL" and len(panel["rows"]) == 33
begin = time.monotonic()
B = PolynomialRing(GF(2), "u")
u = B.gen()
F = GF(2**41, name="u", modulus=u**41+u**3+1)
E = EllipticCurve(F, [1, 0, 0, 0, 1])
dec = F.from_integer
enc = lambda value: sum(int(bit) << i for i, bit in enumerate(value.polynomial().list()))
states = [{} for _ in range(5)]
lines = Path(cfg["sources"]["join_input"]["path"]).read_text().splitlines()
assert lines[0] == "W11FIVE 5 1124 1"
for line in lines[2:]:
    cols = line.split()
    if cols[0] != "S":
        continue
    slot, sid, code, branch, mask_a, mask_b, col_a, col_b, x, y = map(int, cols[1:])
    states[slot][sid] = E(dec(x), dec(y))
Q = E(*(dec(value) for value in panel["target_point"]))
minus_q = -Q

def determinant(points):
    rows = []
    for point in points + [minus_q]:
        x, y = point[0], point[1]
        rows.append([F.one(), x, y, x*x, x*y, x*x*x])
    return matrix(F, rows).det()

def parity(value):
    return value.bit_count() & 1

output = []
positive_hits = random_hits = random_certificates = 0
for index, row in enumerate(panel["rows"]):
    if time.monotonic() - begin >= cfg["wall_cap_seconds"]:
        status = "WALL_CAP_PARTIAL"
        break
    options = [[states[slot][sid] for sid in row["sign_state_ids"][slot]]
               for slot in range(5)]
    for pair in options:
        assert pair[0][0] == pair[1][0] and pair[0] == -pair[1]
    assert all(enc(options[slot][0][0]) == row["x_coordinates"][slot]
               for slot in range(5))
    base = [options[slot][0] for slot in range(5)]
    coefficient_start = time.monotonic()
    d0 = determinant(base)
    singleton = [determinant([options[slot][int(slot == j)] for slot in range(5)])
                 for j in range(5)]
    linear = [value + d0 for value in singleton]
    quadratic = {}
    for i, j in itertools.combinations(range(5), 2):
        value = determinant([options[slot][int(slot == i or slot == j)]
                             for slot in range(5)])
        quadratic[(i, j)] = value + d0 + linear[i] + linear[j]
    coefficient_seconds = time.monotonic() - coefficient_start
    coeffs = [d0] + linear + list(quadratic.values())
    coeffints = [enc(value) for value in coeffs]
    rows_f2 = matrix(GF(2), 16, 41,
                     lambda r, c: (coeffints[r] >> c) & 1)
    rhs = vector(GF(2), [1] + [0]*15)
    consistent = rows_f2.augment(rhs.column()).rank() == rows_f2.rank()
    separator = None
    if consistent:
        solution = rows_f2.solve_right(rhs)
        separator = sum(int(solution[i]) << i for i in range(41))
        assert parity(separator & coeffints[0]) == 1
        assert all(parity(separator & value) == 0 for value in coeffints[1:])
    matched_signs = []
    for mask in range(32):
        points = [options[j][mask >> j & 1] for j in range(5)]
        expected = d0
        for j in range(5):
            if mask >> j & 1:
                expected += linear[j]
        for (i, j), value in quadratic.items():
            if (mask >> i & 1) and (mask >> j & 1):
                expected += value
        actual = determinant(points)
        assert actual == expected, (index, mask)
        group_hit = sum(points, E(0)) == Q
        assert (actual == 0) == group_hit, (index, mask)
        if separator is not None:
            assert parity(separator & enc(actual)) == 1
        if group_hit:
            matched_signs.append(mask)
    if row["kind"] == "independently_replayed_public_relation":
        assert matched_signs and separator is None
        positive_hits += 1
    else:
        random_hits += bool(matched_signs)
        random_certificates += separator is not None
    output.append({"index": index, "kind": row["kind"],
                   "codes": row["chosen_codes"], "matched_signs": matched_signs,
                   "certificate_mask": separator,
                   "coefficient_span_rank": int(rows_f2.rank()),
                   "quadratic_nonzero_count": sum(value != 0 for value in quadratic.values()),
                   "coefficient_seconds": coefficient_seconds})
    if resource.getrusage(resource.RUSAGE_SELF).ru_maxrss > cfg["rss_cap_bytes"]:
        status = "RSS_CAP_PARTIAL"
        break
else:
    status = "COMPLETE_SIGN_SCREEN"
result = {"status": status, "candidate_id": None,
          "curve_id": cfg["curve_id"], "target_point": panel["target_point"],
          "families_completed": len(output), "random_families": 32,
          "positive_hit_families": positive_hits, "random_hit_families": random_hits,
          "random_certificate_families": random_certificates,
          "rows": output, "wall_seconds": time.monotonic() - begin,
          "peak_rss_raw": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
          "protocol_sha256": sha(HERE/"run_protocol.json"),
          "script_sha256": sha(Path(__file__))}
(HERE/"result.json").write_text(json.dumps(result, indent=2, sort_keys=True)+"\n")
print(json.dumps({key: result[key] for key in ("status", "families_completed",
                                           "random_certificate_families",
                                           "random_hit_families", "wall_seconds")}, sort_keys=True), flush=True)
