"""Clear denominators in S3 after replacing u=z/(1+z), z=1/x."""

import json
from pathlib import Path
from sage.all import GF, PolynomialRing

HERE = Path(__file__).resolve().parent


def main():
    R = PolynomialRing(GF(2), ["c", "t"])
    c, t = R.gens()
    S = PolynomialRing(R, "d")
    d = S.gen()
    A, B, C = 1 + c, 1 + d, 1 + t
    E = A * B * C
    e1 = c * B * C + d * A * C + t * A * B
    e2 = c * d * C + c * t * B + d * t * A
    e3 = c * d * t
    F = e3**2 + e3 * (e1 + e2 + E) + e1**2
    assert F.degree() <= 2
    coeff = [str(F[i]) for i in range(3)]
    result = {"status": "EXACT_S3_CLEARED_IN_INVERSE_X_CHART",
              "coefficients_by_d_degree": coeff, "expanded": str(F),
              "coefficient_ring": "GF(2)[c,t]",
              "identity": "F = E^2 * S3(c/(1+c),d/(1+d),t/(1+t))"}
    (HERE / "s3_identity.json").write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
