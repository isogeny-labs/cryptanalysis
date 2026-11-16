"""Independent finite-field replay of the centered rank-one lift law."""

import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
INPUT = HERE.parent / "xedni-large-order-admission-20261115" / "result.json"
O = None


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def add(a, b, p):
    if a is O:
        return b
    if b is O:
        return a
    x1, y1 = a
    x2, y2 = b
    if x1 == x2 and (y1 + y2) % p == 0:
        return O
    if a == b:
        slope = ((3 * x1 * x1 - 1) * pow(2 * y1, -1, p)) % p
    else:
        slope = ((y2 - y1) * pow(x2 - x1, -1, p)) % p
    x3 = (slope * slope - x1 - x2) % p
    y3 = (slope * (x1 - x3) - y1) % p
    return x3, y3


def mul(k, a, p):
    if k < 0:
        return mul(-k, (a[0], -a[1] % p), p)
    result = O
    while k:
        if k & 1:
            result = add(result, a, p)
        a = add(a, a, p)
        k >>= 1
    return result


def centered(u, q):
    return u if u <= q // 2 else u - q


def main():
    protocol = json.loads((HERE / "protocol.json").read_text())
    result = json.loads((HERE / "result.json").read_text())
    selection = json.loads(INPUT.read_text())
    assert result["status"] == "PASS"
    assert result["protocol_sha256"] == sha(HERE / "protocol.json")
    assert result["source_sha256"] == sha(HERE / "run.py")
    assert result["sage_runtime_sha256"] == sha(HERE / "sage-runtime-info.json")
    assert result["input_sha256"] == sha(INPUT) == \
        protocol["input_selection_result_sha256"]
    assert result["rational_rank"] == 1
    assert result["rational_torsion_order"] == 1
    assert result["rational_generator"] == [2, 2]
    selected = [x for x in selection["rows"] if x["selected"]]
    assert len(result["rows"]) == len(selected)
    L = protocol["coefficient_radius_L"]
    for item, row in zip(selected, result["rows"]):
        p, q = item["field_prime"], item["subgroup_order"]
        P = (2, 2)
        assert (P[1] ** 2 - (P[0] ** 3 - P[0] - 2)) % p == 0
        p_order = next(k for k in range(1, item["curve_order"] + 1)
                       if mul(k, P, p) is O)
        assert p_order == row["rational_generator_reduction_order"]
        assert p_order % q == 0
        m = p_order // q
        G = mul(m, P, p)
        assert mul(q, G, p) is O and G is not O
        Q = mul(17, G, p)
        coords = []
        for t in range(q):
            k = m * centered((17 - t) % q, q)
            assert mul(k, P, p) == add(Q, mul(-t, G, p), p)
            coords.append(k)
        max_abs = max(map(abs, coords))
        K = 2 * L * max_abs
        c_min = K // L
        expected = {"field_prime": p, "subgroup_order": q,
                    "rational_generator_reduction_order": p_order,
                    "subgroup_multiplier_m": m,
                    "offsets_checked": q,
                    "max_abs_single_coordinate": max_abs,
                    "two_point_sum_coordinate_radius_K": K,
                    "minimum_integer_slope_c": c_min,
                    "rank_gap_count_at_minimum_slope": 2 * c_min + 1 < L,
                    "frozen_rank_gap_count_at_c_one": 3 < L,
                    "frozen_coordinate_premise_at_c_one": K <= L}
        assert row == expected
        assert max_abs == m * (q - 1) // 2
    print(json.dumps({"schema": "xedni-rank-one-coordinate-control-audit-v1",
                      "status": "PASS", "fields": len(selected),
                      "offsets_checked": sum(x["subgroup_order"] for x in selected)},
                     sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
