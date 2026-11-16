"""Checked-Sage rank-one rational lift coordinate control."""

import hashlib
import json
from pathlib import Path

from sage.all import EllipticCurve, GF, QQ


HERE = Path(__file__).resolve().parent
INPUT = HERE.parent / "xedni-large-order-admission-20261115" / "result.json"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def centered(residue, q):
    return residue if residue <= q // 2 else residue - q


def main():
    protocol = json.loads((HERE / "protocol.json").read_text())
    assert protocol["schema"] == "xedni-rank-one-coordinate-control-protocol-v1"
    assert sha(INPUT) == protocol["input_selection_result_sha256"]
    selection = json.loads(INPUT.read_text())
    assert selection["status"] == "PASS"
    E = EllipticCurve(QQ, protocol["base_curve_coefficients"])
    P = E(*protocol["rational_generator"])
    assert int(E.rank(proof=True)) == 1
    assert int(E.torsion_order()) == 1
    assert list(E.gens(proof=True)) == [P]
    L = protocol["coefficient_radius_L"]
    rows = []
    for item in selection["rows"]:
        if not item["selected"]:
            continue
        p, q = item["field_prime"], item["subgroup_order"]
        Ep = EllipticCurve(GF(p), protocol["base_curve_coefficients"])
        Pp = Ep(*protocol["rational_generator"])
        p_order = int(Pp.order())
        assert p_order % q == 0
        m = p_order // q
        G = m * Pp
        assert int(G.order()) == q
        Q = 17 * G
        values = []
        for t in range(q):
            k = centered((17 - t) % q, q)
            assert (m * k) * Pp == Q - t * G
            values.append(m * k)
        max_abs = max(map(abs, values))
        assert max_abs == m * (q - 1) // 2
        K = 2 * L * max_abs
        c_min = K // L
        assert K == L * c_min
        rows.append({"field_prime": p, "subgroup_order": q,
                     "rational_generator_reduction_order": p_order,
                     "subgroup_multiplier_m": m,
                     "offsets_checked": q,
                     "max_abs_single_coordinate": max_abs,
                     "two_point_sum_coordinate_radius_K": K,
                     "minimum_integer_slope_c": c_min,
                     "rank_gap_count_at_minimum_slope": 2 * c_min + 1 < L,
                     "frozen_rank_gap_count_at_c_one": 3 < L,
                     "frozen_coordinate_premise_at_c_one": K <= L})
    result = {"schema": "xedni-rank-one-coordinate-control-result-v1",
              "status": "PASS", "protocol_sha256": sha(HERE / "protocol.json"),
              "source_sha256": sha(Path(__file__)),
              "input_sha256": sha(INPUT),
              "sage_runtime_sha256": sha(HERE / "sage-runtime-info.json"),
              "rational_rank": 1, "rational_torsion_order": 1,
              "rational_generator": list(protocol["rational_generator"]),
              "rows": rows}
    print(json.dumps(result, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
