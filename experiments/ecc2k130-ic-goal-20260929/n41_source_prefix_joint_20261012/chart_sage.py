"""Check all new group hits lie in the exact nonexceptional S3 chart."""

import hashlib
import json
from pathlib import Path

from sage.all import EllipticCurve, GF, PolynomialRing

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


protocol = json.loads((HERE / "chart_protocol.json").read_text())
for path, digest in protocol["sources"].items():
    assert sha(path) == digest, path
audit = json.loads((HERE / "sage_audit_result.json").read_text())
ring = PolynomialRing(GF(2), "t")
t = ring.gen()
field = GF(2**41, name="t", modulus=t**41 + t**3 + 1)
curve = EllipticCurve(field, [1, 0, 0, 0, 1])


def dec(n):
    return field(ring([(int(n) >> i) & 1 for i in range(41)]))


def s3(a, b, z):
    product = a * b
    return (1 + product**2) * z**2 + product * z + (a + b)**2 == 0


results = []
for relation in audit["relations"]:
    points = [curve(*map(dec, item["point"])) for item in relation["pairs"]]
    assert all(point != curve(0) and point[0] != 0 for point in points)
    middle = [points[0] + points[1], points[2] + points[3]]
    assert all(point != curve(0) and point[0] != 0 for point in middle)
    target = middle[0] + middle[1]
    assert target != curve(0) and target[0] != 0
    assert all(s3(1 / points[2 * i][0], 1 / points[2 * i + 1][0],
                  1 / middle[i][0]) for i in range(2))
    assert s3(1 / middle[0][0], 1 / middle[1][0], 1 / target[0])
    results.append({"label": relation["label"],
                    "nonexceptional_pair_outputs": 4,
                    "nonexceptional_intermediate_sums": 2,
                    "exact_s3_links": 3,
                    "raw_sum_matches": True})
result = {"status": "PASS_INDEPENDENT_N41_NONEXCEPTIONAL_S3_CHART",
          "candidate_id": None, "relations": results,
          "audit_protocol_sha256": sha(HERE / "chart_protocol.json"),
          "source_sha256": sha(__file__)}
with (HERE / "chart_audit_result.json").open("x") as out:
    json.dump(result, out, sort_keys=True, indent=2)
    out.write("\n")
print(result["status"], len(results))
