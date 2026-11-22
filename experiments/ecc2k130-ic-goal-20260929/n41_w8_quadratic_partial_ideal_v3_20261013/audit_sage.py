"""Independent Sage replay of selected quadratic-region geometry and S3."""

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
source = json.loads((HERE / "protocol.json").read_text())
chosen = [(index, native["cases"][index]) for index in protocol["case_indexes"]]

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
for _, row in chosen:
    width = 1 << row["free_state_bits_per_slot"]
    for slot, start in enumerate(row["starts"]):
        needed.update((slot, sid) for sid in range(start, start + width))
states = {}
target = None
for line in Path(source["source_table"]).open():
    parts = line.split()
    if not parts:
        continue
    if parts[0] == "T" and int(parts[1]) == 1:
        target = curve(decode(int(parts[2])), decode(int(parts[3])))
    if parts[0] == "S":
        slot, sid = int(parts[1]), int(parts[2])
        if (slot, sid) in needed:
            states[(slot, sid)] = (
                curve(decode(int(parts[9])), decode(int(parts[10]))),
                frozenset((int(parts[5]), int(parts[6]))))
assert len(states) == len(needed) and target is not None
t = 1 / target[0]
assert encode(t) == native["target_reciprocal"] == 344545435656


def partials(slot, starts, width):
    output = []
    for a in range(starts[slot], starts[slot] + width):
        pa, ca = states[(slot, a)]
        for b in range(starts[slot + 1], starts[slot + 1] + width):
            pb, cb = states[(slot + 1, b)]
            if ca & cb:
                continue
            total = pa + pb
            if total == curve(0) or total[0] == 0:
                continue
            output.append((total, encode(1 / total[0]), ca | cb))
    return output


checks = []
for index, row in chosen:
    width = 1 << row["free_state_bits_per_slot"]
    starts = row["starts"]
    left = partials(0, starts, width)
    right = partials(2, starts, width)
    C = sorted({entry[1] for entry in left})
    D = sorted({entry[1] for entry in right})
    cr, dr = rank(C), rank(D)
    onehot = bool(C and D and len(C) == cr and len(D) == dr)
    assert (len(left), len(right), len(C), len(D), cr, dr, onehot) == (
        row["left_partial_points"], row["right_partial_points"],
        row["left_unique_reciprocals"], row["right_unique_reciprocals"],
        row["left_span_rank"], row["right_span_rank"],
        row["exact_quadratic_one_hot_ideal"])
    right_index = {}
    for point, coordinate, columns in right:
        right_index.setdefault(xy(point), []).append(columns)
    group_hits = 0
    for point, coordinate, columns in left:
        for other in right_index.get(xy(target - point), []):
            if not columns & other:
                group_hits += 1
    assert group_hits == row["exact_group_hits"]
    s3 = None
    if width <= 8:
        s3 = 0
        for c_word in C:
            c = decode(c_word)
            for d_word in D:
                d = decode(d_word)
                z = t * c * d
                s3 += int(z*z + z + c*c + d*d + t*t == 0)
        assert s3 == row["s3_coordinate_pairs"]
    checks.append({"case_index": index, "width": width,
                   "left_unique": len(C), "right_unique": len(D),
                   "left_rank": cr, "right_rank": dr,
                   "onehot": onehot, "group_hits": group_hits,
                   "direct_s3_coordinate_hits": s3})
    print("AUDIT_CASE", index, flush=True)

result = {"status": "PASS_INDEPENDENT_W8_QUADRATIC_PARTIAL_IDEAL_REPLAY",
          "checks": checks,
          "source_sha256": {"protocol": hashlib.sha256((HERE / "audit_protocol.json").read_bytes()).hexdigest(),
                            "script": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                            "native_result": hashlib.sha256((HERE / "result.json").read_bytes()).hexdigest()}}
with (HERE / "audit_result.json").open("x") as stream:
    json.dump(result, stream, indent=2, sort_keys=True)
    stream.write("\n")
print(result["status"], len(checks))
