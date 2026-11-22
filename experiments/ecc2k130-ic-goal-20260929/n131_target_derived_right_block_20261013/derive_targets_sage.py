"""Derive every raw preimage and right-block root from the public point."""

import hashlib
import json
import sys
import time
from pathlib import Path

from sage.all import EllipticCurve, GF, PolynomialRing


HERE = Path(__file__).resolve().parent
GOAL = HERE.parent
if len(sys.argv) != 2:
    raise SystemExit("usage: derive_targets_sage.py output.json")
output_path = Path(sys.argv[1]).resolve()
assert output_path.parent == HERE and not output_path.exists()
protocol = json.loads((HERE / "protocol.json").read_text())
assert protocol["status"] == "FROZEN"
for path, digest in protocol["sources"].items():
    assert hashlib.sha256(Path(path).read_bytes()).hexdigest() == digest, path

started = time.monotonic_ns()
base = PolynomialRing(GF(2), "t")
t = base.gen()
field = GF(2**131, name="t", modulus=t**131+t**13+t**2+t+1)
curve = EllipticCurve(field, [1,0,0,0,1])
ring = PolynomialRing(field, "v")
O = curve(0)


def decode(value):
    return field(base([(int(value) >> i) & 1 for i in range(131)]))


def encode(value):
    return sum(int(bit) << i for i, bit in enumerate(value.polynomial().list()))


def point_record(point):
    return [encode(point[0]), encode(point[1])]


Q = curve(*map(decode, protocol["public_target"]))
assert protocol["subgroup_order"]*Q == O
inverse_four = pow(4, -1, protocol["subgroup_order"])
base_preimage = inverse_four*Q
assert 4*base_preimage == Q
torsion = None
torsion_lift_x_code = None
for code in range(1, protocol["torsion_search_max_x_code"]+1):
    for point in sorted(curve.lift_x(decode(code), all=True),
                        key=lambda P: encode(P[1])):
        candidate = protocol["subgroup_order"]*point
        if candidate != O and 2*candidate != O and 4*candidate == O:
            torsion = candidate
            torsion_lift_x_code = code
            break
    if torsion is not None:
        break
assert torsion is not None
preimages = [base_preimage+i*torsion for i in range(4)]
assert len(set(point_record(point)[0] for point in preimages)) == 4
assert all(4*point == Q for point in preimages)
fixture = json.loads((GOAL / "n131_w18_allseed_fourpair_20261012/n131_control_fixture.json").read_text())
fixture_raw = curve(*map(decode, fixture["raw_target"]))
assert fixture_raw in preimages
left = decode(protocol["left_block_reciprocal"])
rows = []
for index, raw in enumerate(preimages):
    if raw == O or raw[0] == 0:
        rows.append({"preimage_index": index, "raw_point": point_record(raw),
                     "chart_status": "EXCEPTIONAL_RECIPROCAL", "right_roots": []})
        continue
    target = 1/raw[0]
    A = 1+(left*target)**2
    B = left*target
    C = target**2+left**2
    polynomial = ring([C,B,A])
    assert polynomial != 0
    roots = sorted([value for value, _ in polynomial.roots()], key=encode)
    assert all(polynomial(value) == 0 for value in roots)
    rows.append({"preimage_index": index, "raw_point": point_record(raw),
                 "chart_status": "FINITE_ROOTS",
                 "raw_target_reciprocal": encode(target),
                 "upper_degree": int(polynomial.degree()),
                 "right_roots": [encode(value) for value in roots]})
all_roots = [value for row in rows for value in row["right_roots"]]
assert fixture["intermediate_reciprocals"][1] in all_roots
output = {
    "status": "PASS_PUBLIC_POINT_TO_ALL_RIGHT_BLOCK_CANDIDATES",
    "target_count": 1, "curve_id": protocol["curve_id"],
    "public_target": protocol["public_target"],
    "left_block_reciprocal": protocol["left_block_reciprocal"],
    "preimage_count": 4, "candidate_count": len(all_roots),
    "distinct_candidate_count": len(set(all_roots)),
    "fixture_right_root_present": True,
    "torsion_lift_x_code": torsion_lift_x_code,
    "torsion_point": point_record(torsion),
    "base_preimage": point_record(base_preimage),
    "rows": rows,
    "target_derivation_ns": time.monotonic_ns()-started,
    "source_sha256": {
        "protocol": hashlib.sha256((HERE / "protocol.json").read_bytes()).hexdigest(),
        "script": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    },
}
with output_path.open("x") as stream:
    json.dump(output, stream, indent=2, sort_keys=True)
    stream.write("\n")
print(output["status"], output["candidate_count"], output["distinct_candidate_count"], flush=True)
