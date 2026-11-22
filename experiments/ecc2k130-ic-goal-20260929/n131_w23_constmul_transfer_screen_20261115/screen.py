"""Price direct W23 two-edge traversal using a frozen N41 kernel receipt."""

import hashlib
import json
from decimal import Decimal, getcontext
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXP = HERE.parent
PROJECTION = EXP / "n131_w23_sixpair_density_20261016" / "projection_result.json"
KERNEL = EXP / "n41_native_half_affine_constmul_20261115" / "abba_result.json"
PROTOCOL = HERE / "protocol.json"
RESULT = HERE / "result.json"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    p = json.loads(PROTOCOL.read_text())
    assert not RESULT.exists(), "refuse to overwrite frozen screen"
    for name, path in (("projection", PROJECTION), ("kernel", KERNEL),
                       ("screen", Path(__file__))):
        assert sha(path) == p["sha256"][name], name
    projection = json.loads(PROJECTION.read_text())
    kernel = json.loads(KERNEL.read_text())
    assert projection["status"] == "COMPLETE_W23_SIXPAIR_SOURCE_BOUND"
    assert projection["curve_id"] == p["curve_id"]
    assert kernel["status"] == "PASS_FROZEN_N41_CONSTMUL_ABBA"
    e = int(projection["usable_edges_per_slot"])
    degree = int(projection["max_edge_degree_at_folded_column"])
    assert e == p["expected_edges"] and degree == p["expected_degree"]
    # Each edge occupies two columns; at most degree edges at each column
    # collide with one fixed first edge in the next rotated source slot.
    pairs_lower = e * (e - 2 * degree)
    pairs_upper = e * e
    rows = [x["result"] for x in kernel["rows"] if x["name"] == "constmul"]
    assert len(rows) == 2
    assert all(x["families"] == 248640 and x["retained"] == 495 for x in rows)
    getcontext().prec = 60
    best_seconds = min(Decimal(str(x["query_s"])) for x in rows)
    rate = Decimal(248640) / best_seconds
    cap = Decimal(p["wall_cap_seconds"])
    required_rate = Decimal(pairs_lower) / cap
    optimistic_seconds = Decimal(pairs_lower) / rate
    out = {
        "kind": "n131_w23_constmul_direct_transfer_screen_v1",
        "status": "REJECT_DIRECT_PAIR_TRAVERSAL_WITH_N41_RATE_MODEL",
        "protocol_sha256": sha(PROTOCOL),
        "curve_id": p["curve_id"],
        "usable_edges_per_slot": e,
        "max_edge_degree_at_folded_column": degree,
        "ordered_column_disjoint_two_edge_families_lower": pairs_lower,
        "ordered_two_edge_families_upper": pairs_upper,
        "observed_n41_chart_family_combinations": 248640,
        "observed_best_n41_constmul_seconds": str(best_seconds),
        "observed_best_n41_chart_family_rate_per_second": str(rate),
        "n131_required_family_rate_per_second_one_chart": str(required_rate),
        "rate_ratio_required_to_observed": str(required_rate / rate),
        "same_rate_projection_seconds_one_chart": str(optimistic_seconds),
        "wall_cap_seconds": p["wall_cap_seconds"],
        "scope": "Directly visiting all disjoint ordered W23 two-edge families for one residual chart with the N41 optimized per-family rate. The N131 field implementation and complete six-pair search are unmeasured; this is a transfer screen, not an N131 timing or an algorithm-independent lower bound.",
    }
    RESULT.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")
    print(json.dumps(out, sort_keys=True))


if __name__ == "__main__":
    main()
