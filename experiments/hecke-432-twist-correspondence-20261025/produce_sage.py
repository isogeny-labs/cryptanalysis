"""Build the level-432 twist correspondence from the level-27 map."""
from hashlib import sha256
import json
from pathlib import Path

from sage.all import EllipticCurve, Gamma0, LaurentSeriesRing, O, QQ, QuadraticField, kronecker

HERE = Path(__file__).resolve().parent


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def coeffs(series, low, high):
    return {str(n): str(series[n]) for n in range(low, high)}


def main():
    protocol_path = HERE / "protocol.json"
    p = json.loads(protocol_path.read_text())
    assert p["status"] == "FROZEN_BEFORE_PERSISTED_TWIST_RUN_AFTER_EXPLORATORY_IDENTITY"
    A = EllipticCurve(QQ, p["curve_A_ainvs"])
    B = EllipticCurve(QQ, p["curve_B_ainvs"])
    assert int(A.conductor()) == p["curve_A_conductor"]
    assert int(B.conductor()) == p["curve_B_conductor"]
    assert A.quadratic_twist(-1).is_isomorphic(B)
    assert Gamma0(432).index() * 2 // 12 == p["sturm_bound"]
    a = A.q_expansion(p["newform_precision"])
    b = B.q_expansion(p["newform_precision"])
    mismatch = [n for n in range(p["newform_precision"])
                if b[n] != kronecker(p["twist_discriminant"], n) * a[n]]
    assert not mismatch

    precision = p["parametrization_precision"]
    cap = p["comparison_precision_exclusive"]
    xa, ya = A.modular_parametrization().power_series(prec=precision)
    xb, yb = B.modular_parametrization().power_series(prec=precision)
    K = QuadraticField(-1, "i")
    i = K.gen()
    R = LaurentSeriesRing(K, "q")
    q = R.gen()
    AR = EllipticCurve(R, [0, 0, 1, 0, 0])
    P1 = AR(R(xa)(i*q), R(ya)(i*q))
    P3 = AR(R(xa)(-i*q), R(ya)(-i*q))
    D = P1 - P3
    twist_x = -4 * D[0]
    twist_y = -8*i*(D[1] + R(1)/2)
    assert twist_y**2 - twist_x**3 + 16 + O(q**cap) == 0
    assert twist_x + O(q**cap) == R(xb) + O(q**cap)
    assert twist_y + O(q**cap) == R(yb) + O(q**cap)
    assert twist_x.derivative()/(2*twist_y) + O(q**cap) == R(b)/q + O(q**cap)

    output = {
        "status": "PASS_STURM_TWIST_AND_FORMAL_MAP",
        "protocol_sha256": digest(protocol_path),
        "producer_sha256": digest(HERE / "produce_sage.py"),
        "A_conductor": int(A.conductor()), "B_conductor": int(B.conductor()),
        "sturm_bound": p["sturm_bound"],
        "twist_coefficient_mismatches": mismatch,
        "A_newform_coefficients": [int(a[n]) for n in range(p["newform_precision"])],
        "B_newform_coefficients": [int(b[n]) for n in range(p["newform_precision"])],
        "direct_B_X_coefficients": coeffs(xb, -2, cap),
        "direct_B_Y_coefficients": coeffs(yb, -3, cap),
        "twist_X_coefficients": coeffs(twist_x, -2, cap),
        "twist_Y_coefficients": coeffs(twist_y, -3, cap),
        "comparison_precision_exclusive": cap,
        "finite_field_evaluator": None,
        "candidate_id": None,
        "timing_claim": None,
    }
    (HERE / "result.json").write_text(json.dumps(output, sort_keys=True, indent=2) + "\n")
    print(json.dumps({"status": output["status"], "sturm_bound": p["sturm_bound"],
                      "comparison_precision_exclusive": cap}, sort_keys=True))


if __name__ == "__main__":
    main()
