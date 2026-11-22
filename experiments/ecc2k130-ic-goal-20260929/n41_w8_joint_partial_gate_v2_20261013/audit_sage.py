"""Independent Sage replay of W8 witness-centered joint partial-sum spans."""

import hashlib
import json
from pathlib import Path

from sage.all import EllipticCurve, GF, PolynomialRing

HERE = Path(__file__).resolve().parent
protocol = json.loads((HERE / "audit_protocol.json").read_text())
assert protocol["status"] == "FROZEN"
for path, expected in protocol["sources"].items():
    assert hashlib.sha256(Path(path).read_bytes()).hexdigest() == expected, path
native = json.loads((HERE / "result.json").read_text())
table = Path(json.loads((HERE / "protocol.json").read_text())["source_table"])

ring = PolynomialRing(GF(2), "X")
X = ring.gen()
field = GF(2**41, name="X", modulus=X**41 + X**3 + 1)
curve = EllipticCurve(field, [1, 0, 0, 0, 1])


def decode(number):
    return field(ring([(int(number) >> i) & 1 for i in range(41)]))


def encode(value):
    return sum(int(bit) << i for i, bit in enumerate(value.polynomial().list()))


def xy(point):
    return (encode(point[0]), encode(point[1]))


def rank(values):
    pivots = {}
    for value in values:
        while value:
            bit = value.bit_length() - 1
            if bit in pivots:
                value ^= pivots[bit]
            else:
                pivots[bit] = value
                break
    return len(pivots)


needed = set()
for level in native["levels"]:
    width = level["states_per_slot"]
    for slot, start in enumerate(level["positive_starts"]):
        needed.update((slot, sid) for sid in range(start, start + width))
needed.update((slot, sid) for slot in (0, 1) for sid in range(4))
states = {}
target = None
for line in table.open():
    parts = line.split()
    if not parts:
        continue
    if parts[0] == "T" and int(parts[1]) == 1:
        target = curve(decode(int(parts[2])), decode(int(parts[3])))
    if parts[0] == "S":
        slot, sid = int(parts[1]), int(parts[2])
        if (slot, sid) in needed:
            ca, cb = int(parts[5]), int(parts[6])
            point = curve(decode(int(parts[9])), decode(int(parts[10])))
            states[(slot, sid)] = (point, frozenset((ca, cb)))
assert len(states) == len(needed) and target is not None
reciprocal = 1 / target[0]
assert encode(reciprocal) == native["target_reciprocal"] == 344545435656


def partials(slot, start_a, start_b, width):
    result = []
    for a in range(start_a, start_a + width):
        pa, ca = states[(slot, a)]
        for b in range(start_b, start_b + width):
            pb, cb = states[(slot + 1, b)]
            if ca & cb:
                continue
            total = pa + pb
            if total == curve(0) or total[0] == 0:
                continue
            result.append((total, 1 / total[0], ca | cb))
    return result


def independent_basis(words):
    pivots = {}
    result = []
    for word in words:
        reduced = word
        while reduced:
            bit = reduced.bit_length() - 1
            if bit in pivots:
                reduced ^= pivots[bit]
            else:
                pivots[bit] = reduced
                result.append(word)
                break
    return result


checks = []
for level in native["levels"]:
    f = level["free_state_bits_per_slot"]
    width = level["states_per_slot"]
    starts = level["positive_starts"]
    left = partials(0, starts[0], starts[1], width)
    right = partials(2, starts[2], starts[3], width)
    assert len(left) == level["positive_left_partials"]
    assert len(right) == level["positive_right_partials"]
    C = independent_basis([encode(x[1]) for x in left])
    D = independent_basis([encode(x[1]) for x in right])
    assert len(C) == level["positive_left_rank"]
    assert len(D) == level["positive_right_rank"]
    cross = []
    for c in C:
        for d in D:
            z = reciprocal * decode(c) * decode(d)
            cross.append(encode(z*z + z))
    assert rank(cross) == level["positive_cross_rank"]
    right_index = {}
    for point, coordinate, columns in right:
        right_index.setdefault(xy(point), []).append(columns)
    hits = 0
    for point, coordinate, columns in left:
        need = target - point
        for other_columns in right_index.get(xy(need), []):
            if not columns & other_columns:
                hits += 1
    assert hits == level["positive_exact_hits"]
    checks.append({"free_state_bits_per_slot": f, "left_count": len(left),
                   "right_count": len(right), "left_rank": len(C),
                   "right_rank": len(D), "cross_rank": rank(cross),
                   "exact_group_hits": hits})

empty = partials(0, 0, 0, 4)
assert len(empty) == 0
result = {"status": "PASS_INDEPENDENT_W8_JOINT_PARTIAL_SAGE_REPLAY",
          "target_reciprocal": encode(reciprocal),
          "positive_levels": checks,
          "empty_same_edge_control_count": 0,
          "source_sha256": {"protocol": hashlib.sha256((HERE / "audit_protocol.json").read_bytes()).hexdigest(),
                            "script": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                            "native_result": hashlib.sha256((HERE / "result.json").read_bytes()).hexdigest()}}
with (HERE / "audit_result.json").open("x") as stream:
    json.dump(result, stream, indent=2, sort_keys=True)
    stream.write("\n")
print(result["status"], len(checks))
