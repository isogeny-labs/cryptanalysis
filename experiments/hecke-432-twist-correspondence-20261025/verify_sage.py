"""Independent replay: coefficient filter and manual chord law."""
import json
from pathlib import Path

from sage.all import EllipticCurve, LaurentSeriesRing, O, QQ, QuadraticField

HERE = Path(__file__).resolve().parent


def main():
    p = json.loads((HERE / "protocol.json").read_text())
    r = json.loads((HERE / "result.json").read_text())
    a, b = r["A_newform_coefficients"], r["B_newform_coefficients"]
    assert len(a) == len(b) == 145
    for n in range(145):
        chi = 0 if n % 2 == 0 else (1 if n % 4 == 1 else -1)
        assert b[n] == chi*a[n], n
    A = EllipticCurve(QQ, p["curve_A_ainvs"])
    xa, ya = A.modular_parametrization().power_series(prec=p["parametrization_precision"])
    K = QuadraticField(-1, "i")
    i = K.gen()
    R = LaurentSeriesRing(K, "q")
    q = R.gen()
    x1, y1 = R(xa)(i*q), R(ya)(i*q)
    x3, y3 = R(xa)(-i*q), R(ya)(-i*q)
    # On y^2+y=x^3, the negative of (x3,y3) is (x3,-y3-1).
    slope = ((-y3-1) - y1)/(x3-x1)
    xd = slope**2-x1-x3
    yd = -y1-1+slope*(x1-xd)
    X = -4*xd
    Y = -8*i*(yd+R(1)/2)
    cap = p["comparison_precision_exclusive"]
    for n in range(-2, cap):
        assert str(X[n]) == r["direct_B_X_coefficients"][str(n)], ("X", n)
    for n in range(-3, cap):
        assert str(Y[n]) == r["direct_B_Y_coefficients"][str(n)], ("Y", n)
    assert Y**2-X**3+16+O(q**cap) == 0
    out = {"status": "PASS_INDEPENDENT_FILTER_AND_CHORD_REPLAY",
           "coefficient_count": len(a), "map_precision_exclusive": cap,
           "manual_chord_law": True}
    (HERE / "validation.json").write_text(json.dumps(out, sort_keys=True, indent=2) + "\n")
    print(json.dumps(out, sort_keys=True))


if __name__ == "__main__":
    main()
