"""Decode the native hit to source masks and replay the public group equation."""

import hashlib
import itertools
import json
import time
from pathlib import Path

from sage.all import EllipticCurve, GF, PolynomialRing


HERE = Path(__file__).resolve().parent
GOAL = HERE.parent
audit_protocol = json.loads((HERE / "audit_protocol.json").read_text())
assert audit_protocol["status"] == "FROZEN"
for path, digest in audit_protocol["sources"].items():
    assert hashlib.sha256(Path(path).read_bytes()).hexdigest() == digest, path
started = time.monotonic_ns()
protocol = json.loads((HERE / "protocol.json").read_text())
pipeline = json.loads((HERE / "pipeline_result.json").read_text())
targets = json.loads((HERE / "target_candidates.json").read_text())
fixture = json.loads((GOAL / "n131_w18_allseed_fourpair_20261012/n131_control_fixture.json").read_text())
support = GOAL / "n131_w16_w18_sixpair_width_gate_20261010/support_w18.tsv"
columns = {int(mask): int(column) for mask, column in
           (line.split() for line in support.read_text().splitlines())}
assert len(columns) == 131307
assert pipeline["status"] == "COMPLETE_ALL_TARGET_DERIVED_RIGHT_CANDIDATES"
assert len(pipeline["attempts"]) == 8
assert [row["raw_gcd_hits"] for row in pipeline["attempts"]] == [0,0,0,0,0,1,0,0]
hit_row = pipeline["attempts"][5]
native = json.loads((HERE / "attempt_05/native_result.json").read_text())
assert native["status"] == "COMPLETE_ALGEBRAIC_SCAN"
assert native["processed_product_states"] == 32827
assert len(native["hits"]) == 1 and native["hits"][0]["gcd_degree"] == 1
base = PolynomialRing(GF(2), "t")
t = base.gen()
field = GF(2**131, name="t", modulus=t**131+t**13+t**2+t+1)
curve = EllipticCurve(field, [1,0,0,0,1])
O = curve(0)


def decode(value):
    return field(base([(int(value) >> i) & 1 for i in range(131)]))


def encode(value):
    return sum(int(bit) << i for i, bit in enumerate(value.polynomial().list()))


def from_limbs(limbs):
    return decode(sum(int(limb) << (64*i) for i, limb in enumerate(limbs)))


hit = native["hits"][0]
p = from_limbs(hit["p"])
c0, c1 = [from_limbs(value) for value in hit["gcd_coefficients"]]
assert c1 != 0
q = c0/c1
assert c0+c1*q == 0


def inverse_product(value, seed_mask, rotation):
    seed = decode(seed_mask << 1)
    unrotated = value**(1 << (131-rotation)) if rotation else value
    source_bits = [bit for bit in range(18) if bit != seed_mask.bit_length()-1]
    pivots = {}
    for bit in source_bits:
        w = decode(1 << (bit+1))
        vector = encode(w*(w+seed))
        code = 1 << bit
        while vector:
            pivot = vector.bit_length()-1
            if pivot in pivots:
                vector ^= pivots[pivot][0]
                code ^= pivots[pivot][1]
            else:
                pivots[pivot] = (vector, code)
                break
        assert vector
    assert len(pivots) == 17
    remainder = encode(unrotated)
    code = 0
    while remainder:
        pivot = remainder.bit_length()-1
        assert pivot in pivots
        remainder ^= pivots[pivot][0]
        code ^= pivots[pivot][1]
    masks = [code, code ^ seed_mask]
    assert code & (1 << (seed_mask.bit_length()-1)) == 0
    assert masks[0] in columns and masks[1] in columns
    assert columns[masks[0]] != columns[masks[1]]
    assert (decode(masks[0] << 1)*decode(masks[1] << 1))**(1 << rotation) == value
    return masks


right_first = inverse_product(p, 5, 64)
right_second = inverse_product(q, 1, 96)
assert right_first == fixture["masks"][2]
assert right_second == fixture["masks"][3]
all_masks = [*fixture["masks"][0], *fixture["masks"][1],
             *right_first, *right_second]
assert len(set(all_masks)) == 8
all_columns = [columns[mask] for mask in all_masks]
assert len(set(all_columns)) == 8
assert hit_row["right_reciprocal"] == fixture["intermediate_reciprocals"][1]
assert targets["rows"][hit_row["preimage_index"]]["raw_point"] == fixture["raw_target"]


def half_trace(value):
    acc, term = field.zero(), value
    for _ in range(66):
        acc += term
        term = term**4
    assert acc**2+acc == value
    return acc


def diagonal(mask):
    w = decode(mask << 1)
    assert w.trace() == 0
    u = half_trace(w)
    assert u != 0
    raw = curve.lift_x(1+1/u, all=True)[0]
    point = raw+curve(raw[0]**2, raw[1]**2)
    assert point != O and point[0] == 1/w
    return point


def frob(point, rotation):
    if point == O:
        return O
    return curve(point[0]**(1 << rotation), point[1]**(1 << rotation))


points = {mask: diagonal(mask) for mask in all_masks}
r = protocol["subgroup_order"]
assert all(4*point != O and r*(4*point) == O for point in points.values())
rotations = fixture["rotations"]
source_pairs = [all_masks[2*i:2*i+2] for i in range(4)]
pair_states = [[(signs, frob(signs[0]*points[pair[0]]+
                              signs[1]*points[pair[1]], rotation))
                for signs in itertools.product((1,-1), repeat=2)]
               for pair, rotation in zip(source_pairs, rotations)]
Q = curve(*map(decode, protocol["public_target"]))
assert r*Q == O
matches = []
for choices in itertools.product(*pair_states):
    raw_sum = sum((point for _, point in choices), O)
    if 4*raw_sum == Q:
        matches.append({"signs": [list(sign) for sign, _ in choices],
                        "raw_point": [encode(raw_sum[0]), encode(raw_sum[1])]})
assert matches
assert any(row["raw_point"] == fixture["raw_target"] for row in matches)
output = {
    "status": "PASS_TARGET_DERIVED_N131_RIGHT_SOURCE_AND_GROUP_REPLAY",
    "target_count": 1, "target_kind": "constructed_correctness_control",
    "candidate_index": 5, "raw_gcd_hit_count": 1,
    "decoded_first_product": encode(p), "decoded_second_product": encode(q),
    "right_source_pairs": [right_first, right_second],
    "all_masks": all_masks, "all_folded_columns": all_columns,
    "signed_assignments_checked": 256,
    "public_group_matches": matches,
    "audit_wall_ns": time.monotonic_ns()-started,
    "source_sha256": {
        "audit_protocol": hashlib.sha256((HERE / "audit_protocol.json").read_bytes()).hexdigest(),
        "pipeline_result": hashlib.sha256((HERE / "pipeline_result.json").read_bytes()).hexdigest(),
        "native_hit": hashlib.sha256((HERE / "attempt_05/native_result.json").read_bytes()).hexdigest(),
        "script": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    },
}
with (HERE / "audit_result.json").open("x") as stream:
    json.dump(output, stream, indent=2, sort_keys=True)
    stream.write("\n")
print(output["status"], len(matches), flush=True)
