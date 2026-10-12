"""Checked-Sage replay of the positive N41 functional S3 root chart."""

import hashlib
import json
from pathlib import Path

from sage.all import EllipticCurve, GF, PolynomialRing

HERE = Path(__file__).resolve().parent
GOAL = HERE.parent
INPUT = GOAL / "n41_w8_sixpair_mitm_20261011/join_input.tsv"
PARENT = GOAL / "n41_w8_tenpair_density_control_20261012/audit_result.json"
SLOTS = (0, 1, 2, 3, 4, 5, 0, 1, 2, 3)
TREE = ((0, 1), (2, 3), (4, 5), (6, 7), (10, 11),
        (12, 13), (14, 15), (16, 8), (17, 9))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


protocol = json.loads((HERE / "audit_protocol.json").read_text())
assert protocol["status"] == "FROZEN_BEFORE_FUNCTIONAL_CHART_SAGE_AUDIT"
for path, digest in protocol["sources"].items():
    assert sha(path) == digest, path
chart = json.loads((HERE / "positive_chart.json").read_text())
parent = json.loads(PARENT.read_text())
assert parent["source_edges_distinct"] == 10
assert chart["state_ids"] == [row["state_id"] for row in parent["source_pairs"]]
assert chart["target_index"] == parent["raw_target_preimage_index"] == 1

ring = PolynomialRing(GF(2), "t")
t = ring.gen()
field = GF(2**41, name="t", modulus=t**41 + t**3 + 1)
curve = EllipticCurve(field, [1, 0, 0, 0, 1])


def decode(value):
    return field(ring([(int(value) >> i) & 1 for i in range(41)]))


def encode(value):
    return sum(int(bit) << i for i, bit in enumerate(value.polynomial().list()))


states = {}
targets = {}
for line in INPUT.read_text().splitlines()[1:]:
    parts = line.split()
    if parts[0] == "S":
        slot, sid = int(parts[1]), int(parts[2])
        states[slot, sid] = curve(decode(parts[-2]), decode(parts[-1]))
    elif parts[0] == "T":
        targets[int(parts[1])] = curve(decode(parts[2]), decode(parts[3]))
assert len(states) == 840 and len(targets) == 4
nodes = [states[slot, sid] for slot, sid in zip(SLOTS, chart["state_ids"])]
assert [[encode(point[0]), encode(point[1])] for point in nodes] == chart["point_chain"][:10]


def halftrace(value):
    answer = field.zero()
    for _ in range(21):
        answer += value
        value = value**4
    return answer


checks = []
for index, (left, right) in enumerate(TREE):
    point = nodes[left] + nodes[right]
    assert point != curve(0) and point[0] != 0
    nodes.append(point)
    a, b, z = (1 / nodes[left][0], 1 / nodes[right][0], 1 / point[0])
    p, aa, cc = a * b, 1 + (a * b)**2, (a + b)**2
    assert aa * z**2 + p * z + cc == 0
    bit = chart["branch_bits"][index]
    if aa == 0:
        produced = cc
    else:
        arg = aa * cc / p**2
        h = halftrace(arg)
        assert h**2 + h == arg
        produced = (p / aa) * (h + bit)
    assert produced == z
    checks.append({"index": index, "branch": bit, "a_equals_zero": aa == 0,
                   "output_z": encode(z)})
assert [[encode(point[0]), encode(point[1])] for point in nodes] == chart["point_chain"]
assert nodes[-1] == targets[chart["target_index"]]
assert [encode(nodes[-1][0]), encode(nodes[-1][1])] == chart["target_point"]
result = {"status": "PASS_INDEPENDENT_SAGE_N41_FUNCTIONAL_ROOT_CHART",
          "curve_id": "EC1N41Ckb1h7d5e80d3c4d0",
          "source_points": 10, "root_links": len(checks), "checks": checks,
          "target_index": chart["target_index"],
          "protocol_sha256": sha(HERE / "audit_protocol.json")}
with (HERE / "audit_result.json").open("x") as stream:
    json.dump(result, stream, sort_keys=True, indent=2)
    stream.write("\n")
print(result["status"], len(checks))
