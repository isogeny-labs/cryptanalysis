"""Test approximate coordinate characters on source pair additions."""

import hashlib
import json
import time
from pathlib import Path

from sage.all import EllipticCurve, GF, PolynomialRing

HERE = Path(__file__).resolve().parent
GOAL = HERE.parent
protocol = json.loads((HERE / "protocol.json").read_text())
assert protocol["status"] == "FROZEN_BEFORE_N41_NEAR_CHARACTER_PANEL"
for path, digest in protocol["sources"].items():
    assert hashlib.sha256(Path(path).read_bytes()).hexdigest() == digest, path
base = PolynomialRing(GF(2), "t")
t = base.gen()
field = GF(2**41, name="t", modulus=t**41 + t**3 + 1)
curve = EllipticCurve(field, [1, 0, 0, 0, 1])
r = 549756390943


def decode(value):
    return field(base([(int(value) >> i) & 1 for i in range(41)]))


def encode(value):
    return sum(int(bit) << i for i, bit in enumerate(value.polynomial().list()))


states = [[], []]
with (GOAL / "n131_w18_allseed_fourpair_20261012/n41_diagonal/pairs.tsv").open() as source:
    assert source.readline().strip() == "ECC2K41_ALLSEED4 4 4"
    for line in source:
        row = line.split()
        if row[0] != "S" or int(row[1]) not in (0, 1):
            continue
        slot = int(row[1])
        point = curve(decode(row[9]), decode(row[10]))
        states[slot].append((point, frozenset((int(row[5]), int(row[6])))))
assert list(map(len, states)) == [30952, 30952]
generator = states[0][0][0]
assert generator != curve(0) and r * generator == curve(0)


def hash_number(tag, i, attempt, offset=0):
    payload = f"{tag}:{i}:{attempt}".encode()
    digest = hashlib.sha256(payload).digest()
    return int.from_bytes(digest[offset:offset+8], "big")


def error_row(p, q):
    summation = p + q
    assert p != curve(0) and q != curve(0) and summation != curve(0)
    assert p[0] != 0 and q[0] != 0 and summation[0] != 0
    x_error = p[0] + q[0] + summation[0]
    inverse_error = 1 / p[0] + 1 / q[0] + 1 / summation[0]
    return [encode(x_error), encode(inverse_error)]


def source_sample(tag, i):
    for attempt in range(100):
        left = hash_number(tag, i, attempt) % len(states[0])
        right = hash_number(tag, i, attempt, 8) % len(states[1])
        p, pc = states[0][left]
        q, qc = states[1][right]
        if len(pc | qc) != 4 or p + q == curve(0):
            continue
        return [left, right, *error_row(p, q)]
    raise AssertionError((tag, i, "no distinct-column source draw"))


def uniform_sample(i):
    for attempt in range(100):
        k = 1 + hash_number("uniform", i, attempt) % (r - 1)
        l = 1 + hash_number("uniform", i, attempt, 8) % (r - 1)
        if (k + l) % r == 0:
            continue
        return [k, l, *error_row(k * generator, l * generator)]
    raise AssertionError((i, "no uniform draw"))


start = time.monotonic_ns()
vectors = {}
for tag, count in (("train", 4096), ("holdout", 8192), ("uniform", 8192)):
    vectors[tag] = [uniform_sample(i) if tag == "uniform" else source_sample(tag, i)
                    for i in range(count)]
    print("SAMPLES", tag, count, time.monotonic_ns() - start, flush=True)

masks = [(1 << i, f"bit_{i}") for i in range(41)]
masks.extend(((1 << i) | (1 << j), f"bits_{i}_{j}")
             for i in range(41) for j in range(i + 1, 41))
assert len(masks) == 861


def signed_count(rows, coordinate, mask):
    zeros = sum(((row[coordinate] & mask).bit_count() & 1) == 0 for row in rows)
    return 2 * zeros - len(rows)


selection = {}
for coordinate, label in ((2, "x"), (3, "inverse_x")):
    train = [{"mask": mask, "label": name,
              "signed_count": signed_count(vectors["train"], coordinate, mask)}
             for mask, name in masks]
    train.sort(key=lambda row: (-abs(row["signed_count"]), row["mask"]))
    selected = []
    for row in train[:10]:
        selected.append({**row,
                         "holdout_signed_count": signed_count(vectors["holdout"], coordinate, row["mask"]),
                         "uniform_signed_count": signed_count(vectors["uniform"], coordinate, row["mask"])})
    selection[label] = {"top_ten": selected, "train_signed_counts": train}

with (HERE / "vectors.json").open("x") as stream:
    json.dump(vectors, stream, separators=(",", ":"), sort_keys=True)
    stream.write("\n")
output = {"status": "PASS_N41_NEAR_CHARACTER_PANEL", "candidate_id": None,
          "source_states_per_slot": [len(s) for s in states], "masks_tested_per_coordinate": 861,
          "samples": {key: len(value) for key, value in vectors.items()},
          "selection": selection, "elapsed_ns": time.monotonic_ns() - start,
          "vectors_sha256": hashlib.sha256((HERE / "vectors.json").read_bytes()).hexdigest(),
          "protocol_sha256": hashlib.sha256((HERE / "protocol.json").read_bytes()).hexdigest()}
with (HERE / "result.json").open("x") as stream:
    json.dump(output, stream, sort_keys=True, indent=2)
    stream.write("\n")
print(output["status"], flush=True)
