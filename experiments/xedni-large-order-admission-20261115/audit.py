"""Independent integer-arithmetic audit of the Sage admission selection."""

import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def is_prime(n):
    if n < 2:
        return False
    for d in range(2, int(n**0.5) + 1):
        if n % d == 0:
            return False
    return True


def curve_order(p):
    # Affine points: for each x, 1 + the quadratic character of x^3-x-2.
    nonzero_squares = {(y * y) % p for y in range(1, p)}
    count = 1  # identity
    for x in range(p):
        value = (x * x * x - x - 2) % p
        count += 1 if value == 0 else (2 if value in nonzero_squares else 0)
    return count


def factor(n):
    result = []
    d = 2
    while d * d <= n:
        if n % d:
            d += 1
            continue
        exponent = 0
        while n % d == 0:
            n //= d
            exponent += 1
        result.append([d, exponent])
        d += 1
    if n > 1:
        result.append([n, 1])
    return result


def main():
    protocol = json.loads((HERE / "protocol.json").read_text())
    result = json.loads((HERE / "result.json").read_text())
    assert result["schema"] == "xedni-large-order-admission-result-v1"
    assert result["protocol_sha256"] == sha(HERE / "protocol.json")
    assert result["source_sha256"] == sha(HERE / "run.py")
    assert result["sage_runtime_sha256"] == sha(HERE / "sage-runtime-info.json")
    lo, hi = protocol["scan_primes_inclusive"]
    qlo, qhi = protocol["subgroup_order_band_inclusive"]
    a = protocol["admission"]
    selected = []
    screened = []
    for p in range(lo, hi + 1):
        if not is_prime(p):
            continue
        assert (-16 * (4 * (-1) ** 3 + 27 * (-2) ** 2)) % p != 0
        order = curve_order(p)
        factors = factor(order)
        q = factors[-1][0]
        admitted = qlo <= q <= qhi
        row = {"field_prime": p, "curve_order": order,
               "order_factorization": factors, "subgroup_order": q,
               "selected": admitted}
        if admitted:
            selected.append(p)
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
        screened.append(row)
        if len(selected) == protocol["take"]:
            break
    assert result["status"] == "PASS"
    assert result["selected_count"] == protocol["take"] == len(selected)
    assert result["screened_count"] == len(screened)
    assert result["rows"] == screened
    assert all(all(row["numeric_gate"][key] for key in (
        "rank_gap", "short_witness", "subgroup_gate"))
        for row in screened if row["selected"])
    print(json.dumps({"schema": "xedni-large-order-admission-audit-v1",
                      "status": "PASS", "selected_primes": selected,
                      "screened_count": len(screened)}, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
