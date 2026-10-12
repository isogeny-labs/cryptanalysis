"""Independent Sage replay of frozen source and uniform-group samples."""

import hashlib
import json
from pathlib import Path

from sage.all import EllipticCurve, GF, PolynomialRing

HERE = Path(__file__).resolve().parent
GOAL = HERE.parent
protocol = json.loads((HERE / "verification_protocol.json").read_text())
assert protocol["status"] == "FROZEN_BEFORE_NEAR_CHARACTER_VERIFICATION"
for path, digest in protocol["sources"].items():
    assert hashlib.sha256(Path(path).read_bytes()).hexdigest() == digest, path
vectors = json.loads((HERE / "vectors.json").read_text())
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
        if row[0] == "S" and int(row[1]) in (0, 1):
            states[int(row[1])].append((curve(decode(row[9]), decode(row[10])),
                                        frozenset((int(row[5]), int(row[6])))))
assert list(map(len, states)) == [30952, 30952]
generator = states[0][0][0]
assert r * generator == curve(0)


def replay(p, q, row):
    summation = p + q
    assert summation != curve(0)
    assert [encode(p[0] + q[0] + summation[0]),
            encode(1 / p[0] + 1 / q[0] + 1 / summation[0])] == row[2:]


checked = {}
for tag in ("train", "holdout", "uniform"):
    for row in vectors[tag][:128]:
        if tag == "uniform":
            p, q = row[0] * generator, row[1] * generator
            assert 1 <= row[0] < r and 1 <= row[1] < r
        else:
            p, pc = states[0][row[0]]
            q, qc = states[1][row[1]]
            assert len(pc | qc) == 4
        replay(p, q, row)
    checked[tag] = 128

output = {"status": "PASS_INDEPENDENT_NEAR_CHARACTER_GROUP_REPLAY",
          "candidate_id": None, "sample_replays": checked,
          "vectors_sha256": hashlib.sha256((HERE / "vectors.json").read_bytes()).hexdigest(),
          "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
with (HERE / "audit.json").open("x") as stream:
    json.dump(output, stream, sort_keys=True, indent=2)
    stream.write("\n")
print(output["status"], checked)
