"""Exhaust the nonzero reciprocal S3 rationality implication at n=5 and 7."""
import hashlib
import json
from pathlib import Path

from sage.all import EllipticCurve, GF, PolynomialRing


D = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    p = json.loads((D / "small_field_protocol_v2.json").read_text())
    assert sha(D / "small_field_s3_v2_sage.py") == p["runner_sha256"]
    panels = []
    for n, terms in ((5, (2, 0)), (7, (1, 0))):
        ring = PolynomialRing(GF(2), "t")
        t = ring.gen()
        modulus = t**n + sum((t**i for i in terms), ring(0))
        assert modulus.is_irreducible()
        field = GF(2**n, name="t", modulus=modulus)
        curve = EllipticCurve(field, [1, 0, 0, 0, 1])
        values = [field(ring([(i >> j) & 1 for j in range(n)]))
                  for i in range(1, 1 << n)]
        rational = {a: len(curve.lift_x(1/a, all=True)) == 2 for a in values}
        checked = solutions = 0
        for c in values:
            if not rational[c]:
                continue
            for a in values:
                for b in values:
                    abc = a * b * c
                    if abc**2 + abc + (a + b + c)**2 != 0:
                        continue
                    solutions += 1
                    assert rational[a] and rational[b]
                    checked += 1
        assert solutions > 0
        panels.append({"field_degree": n, "nonzero_reciprocal_coordinates": len(values),
                       "rational_parent_coordinates": sum(rational.values()),
                       "s3_zeros_with_rational_parent": solutions,
                       "rational_children_checked": checked})
    result = {"status": "PASS_EXHAUSTIVE_SMALL_FIELD_S3_RATIONALITY",
              "protocol_sha256": sha(D / "small_field_protocol_v2.json"),
              "panels": panels}
    (D / "small_field_v2_result.json").write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
