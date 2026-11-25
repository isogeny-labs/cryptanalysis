"""Independently reconstruct the 825 source errors used by rank certificates."""

import hashlib
import json
from pathlib import Path

from sage.all import EllipticCurve, GF, PolynomialRing

HERE = Path(__file__).resolve().parent
GOAL = HERE.parent
PARENT = GOAL / "n41_near_character_20261012"
vectors = json.loads((PARENT / "vectors.json").read_text())["train"]
certificate = json.loads((HERE / "certificate.json").read_text())
assert max(max(v["selected_source_indices"]) for v in certificate["coordinates"].values()) == 824
base = PolynomialRing(GF(2), "t")
t = base.gen()
field = GF(2**41, name="t", modulus=t**41 + t**3 + 1)
curve = EllipticCurve(field, [1, 0, 0, 0, 1])


def decode(value):
    return field(base([(int(value) >> i) & 1 for i in range(41)]))


def encode(value):
    return sum(int(bit) << i for i, bit in enumerate(value.polynomial().list()))


states = [[], []]
with (GOAL / "n131_w18_allseed_fourpair_20261012/n41_diagonal/pairs.tsv").open() as source:
    assert source.readline().strip() == "ECC2K41_ALLSEED4 4 4"
    for line in source:
        item = line.split()
        if item[0] == "S" and int(item[1]) in (0, 1):
            states[int(item[1])].append((curve(decode(item[9]), decode(item[10])),
                                        frozenset((int(item[5]), int(item[6])))))
assert list(map(len, states)) == [30952, 30952]
for row in vectors[:825]:
    p, pc = states[0][row[0]]
    q, qc = states[1][row[1]]
    assert len(pc | qc) == 4
    summed = p + q
    assert summed != curve(0)
    assert [encode(p[0] + q[0] + summed[0]),
            encode(1 / p[0] + 1 / q[0] + 1 / summed[0])] == row[2:]

output = {"status": "PASS_INDEPENDENT_N41_QUADRATIC_RANK_SOURCE_REPLAY",
          "candidate_id": None, "sample_replays": 825,
          "certificate_sha256": hashlib.sha256((HERE / "certificate.json").read_bytes()).hexdigest(),
          "vectors_sha256": hashlib.sha256((PARENT / "vectors.json").read_bytes()).hexdigest(),
          "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
with (HERE / "audit.json").open("x") as stream:
    json.dump(output, stream, sort_keys=True, indent=2)
    stream.write("\n")
print(output["status"], 825)
