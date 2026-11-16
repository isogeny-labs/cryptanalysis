"""Checked-Sage producer for frozen larger-order xedni admission fields."""

import hashlib
import json
from pathlib import Path

from sage.all import EllipticCurve, GF, ZZ, prime_range


HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    protocol = json.loads((HERE / "protocol.json").read_text())
    assert protocol["schema"] == "xedni-large-order-admission-protocol-v1"
    lo, hi = protocol["scan_primes_inclusive"]
    qlo, qhi = protocol["subgroup_order_band_inclusive"]
    take = protocol["take"]
    a = protocol["admission"]
    rows = []
    selected = 0
    for prime in prime_range(lo, hi + 1):
        p = int(prime)
        curve = EllipticCurve(GF(p), protocol["base_curve_coefficients"])
        if curve.discriminant() == 0:
            rows.append({"field_prime": p, "status": "singular"})
            continue
        order = int(curve.cardinality())
        factors = [[int(f), int(e)] for f, e in ZZ(order).factor()]
        q = max(f for f, _ in factors)
        admitted = qlo <= q <= qhi
        row = {"field_prime": p, "curve_order": order,
               "order_factorization": factors, "subgroup_order": q,
               "selected": admitted}
        if admitted:
            selected += 1
            L, arity = a["radius_L"], a["arity"]
            d, c, T, K = (a[k] for k in (
                "rank_d", "coordinate_slope_c", "torsion_label_count_T",
                "coordinate_radius_K"))
            row["numeric_gate"] = {
                "rank_gap": d < arity and K <= c * L and T * (2 * c + 1) ** d < L,
                "short_witness": 2 * L < q,
                "coefficient_box": (4 * L + 1) ** arity - 1,
                "subgroup_gate": (4 * L + 1) ** arity - 1 < q,
            }
            assert all((row["numeric_gate"][key] for key in (
                "rank_gap", "short_witness", "subgroup_gate")))
        rows.append(row)
        if selected == take:
            break
    result = {"schema": "xedni-large-order-admission-result-v1",
              "status": "PASS" if selected == take else "insufficient_fields",
              "protocol_sha256": sha(HERE / "protocol.json"),
              "source_sha256": sha(Path(__file__)),
              "sage_runtime_sha256": sha(HERE / "sage-runtime-info.json"),
              "selected_count": selected, "screened_count": len(rows), "rows": rows}
    print(json.dumps(result, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
