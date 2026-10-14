"""Quadratic one-hot ideal and target S3 gate for W8 two-pair regions."""

import hashlib
import json
import random
from pathlib import Path

from sage.all import EllipticCurve, GF, PolynomialRing

HERE = Path(__file__).resolve().parent
protocol = json.loads((HERE / "protocol.json").read_text())
assert protocol["status"] == "FROZEN"
for path, expected in protocol["sources"].items():
    assert hashlib.sha256(Path(path).read_bytes()).hexdigest() == expected, path

ring = PolynomialRing(GF(2), "X")
X = ring.gen()
field = GF(2**41, name="X", modulus=X**41 + X**3 + 1)
curve = EllipticCurve(field, [1, 0, 0, 0, 1])


def decode(number):
    return field(ring([(int(number) >> i) & 1 for i in range(41)]))


def encode(value):
    return sum(int(bit) << i for i, bit in enumerate(value.polynomial().list()))


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


rng = random.Random(protocol["sampling_seed"])
cases = []
witness = protocol["witness_state_ids"]
for f in (2, 3, 4, 5):
    width = 1 << f
    starts = [(sid // width) * width for sid in witness]
    cases.append((f, "witness", starts))
for f, count in ((2, 64), (3, 32)):
    width = 1 << f
    groups = 30952 // width
    for case_id in range(count):
        starts = [rng.randrange(groups) * width for _ in range(4)]
        cases.append((f, f"sample_{case_id}", starts))

needed = set()
for f, name, starts in cases:
    width = 1 << f
    for slot, start in enumerate(starts):
        needed.update((slot, sid) for sid in range(start, start + width))
states = {}
target = None
for line in Path(protocol["source_table"]).open():
    parts = line.split()
    if not parts:
        continue
    if parts[0] == "T" and int(parts[1]) == protocol["raw_target_index"]:
        target = curve(decode(int(parts[2])), decode(int(parts[3])))
    if parts[0] == "S":
        slot, sid = int(parts[1]), int(parts[2])
        if (slot, sid) in needed:
            state = curve(decode(int(parts[9])), decode(int(parts[10])))
            columns = frozenset((int(parts[5]), int(parts[6])))
            states[(slot, sid)] = (state, columns)
assert len(states) == len(needed) and target is not None
target_reciprocal = 1 / target[0]
assert encode(target_reciprocal) == 344545435656


def partials(slot, starts, width):
    points = []
    coordinates = set()
    for a in range(starts[slot], starts[slot] + width):
        first, columns_a = states[(slot, a)]
        for b in range(starts[slot + 1], starts[slot + 1] + width):
            second, columns_b = states[(slot + 1, b)]
            if columns_a & columns_b:
                continue
            total = first + second
            if total == curve(0) or total[0] == 0:
                continue
            reciprocal = 1 / total[0]
            points.append((total, columns_a | columns_b))
            coordinates.add(encode(reciprocal))
    return points, coordinates


def s3_count(left, right):
    count = 0
    for c_word in left:
        c = decode(c_word)
        for d_word in right:
            d = decode(d_word)
            z = target_reciprocal * c * d
            if z*z + z + c*c + d*d + target_reciprocal*target_reciprocal == 0:
                count += 1
    return count


rows = []
for f, name, starts in cases:
    width = 1 << f
    left_points, left = partials(0, starts, width)
    right_points, right = partials(2, starts, width)
    left_rank, right_rank = rank(left), rank(right)
    exact_one_hot = len(left) == left_rank and len(right) == right_rank
    link_hits = s3_count(left, right) if left and right else 0
    if name == "witness":
        assert link_hits > 0
    rows.append({"free_state_bits_per_slot": f, "name": name, "starts": starts,
                 "left_partial_points": len(left_points),
                 "right_partial_points": len(right_points),
                 "left_unique_reciprocals": len(left),
                 "right_unique_reciprocals": len(right),
                 "left_span_rank": left_rank, "right_span_rank": right_rank,
                 "exact_quadratic_one_hot_ideal": exact_one_hot,
                 "s3_coordinate_pairs": link_hits})

positive_four = next(row for row in rows if row["name"] == "witness" and
                     row["free_state_bits_per_slot"] == 2)
assert positive_four["left_unique_reciprocals"] == positive_four["left_span_rank"] == 8
assert positive_four["right_unique_reciprocals"] == positive_four["right_span_rank"] == 8
# In eight basis bits the quadratic one-hot equations have exactly eight
# solutions: sum bits = 1, and every pairwise product vanishes.
one_hot_solutions = [mask for mask in range(256)
                     if bin(mask).count("1") == 1 and
                     all(not ((mask >> i & 1) and (mask >> j & 1))
                         for i in range(8) for j in range(i + 1, 8))]
assert len(one_hot_solutions) == 8

result = {"status": "COMPLETE_N41_W8_QUADRATIC_PARTIAL_IDEAL_PANEL",
          "target_reciprocal": encode(target_reciprocal),
          "one_hot_eight_bit_solution_count": len(one_hot_solutions),
          "cases": rows,
          "source_sha256": {"protocol": hashlib.sha256((HERE / "protocol.json").read_bytes()).hexdigest(),
                            "script": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}}
with (HERE / "result.json").open("x") as stream:
    json.dump(result, stream, indent=2, sort_keys=True)
    stream.write("\n")
print(result["status"], len(rows))
