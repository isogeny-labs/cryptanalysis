"""Read-only source and arithmetic check for the W23 transfer screen."""

import hashlib
import json
from decimal import Decimal, getcontext
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXP = HERE.parent
PROJECTION = EXP / "n131_w23_sixpair_density_20261016" / "projection_result.json"
KERNEL = EXP / "n41_native_half_affine_constmul_20261115" / "abba_result.json"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    p = json.loads((HERE / "protocol.json").read_text())
    r = json.loads((HERE / "result.json").read_text())
    assert r["protocol_sha256"] == sha(HERE / "protocol.json")
    for key, path in (("projection", PROJECTION), ("kernel", KERNEL),
                      ("screen", HERE / "screen.py")):
        assert p["sha256"][key] == sha(path)
    source = json.loads(PROJECTION.read_text())
    kernel = json.loads(KERNEL.read_text())
    e = source["usable_edges_per_slot"]
    d = source["max_edge_degree_at_folded_column"]
    assert (e, d) == (p["expected_edges"], p["expected_degree"])
    assert r["ordered_column_disjoint_two_edge_families_lower"] == e * (e - 2*d)
    assert r["ordered_two_edge_families_upper"] == e**2
    getcontext().prec = 60
    fast = min(Decimal(str(x["result"]["query_s"])) for x in kernel["rows"]
               if x["name"] == "constmul")
    rate = Decimal(248640) / fast
    lower = Decimal(e * (e - 2*d))
    cap = Decimal(p["wall_cap_seconds"])
    assert Decimal(r["observed_best_n41_constmul_seconds"]) == fast
    assert Decimal(r["observed_best_n41_chart_family_rate_per_second"]) == rate
    assert Decimal(r["n131_required_family_rate_per_second_one_chart"]) == lower/cap
    assert Decimal(r["rate_ratio_required_to_observed"]) == (lower/cap)/rate
    assert Decimal(r["same_rate_projection_seconds_one_chart"]) == lower/rate
    print("PASS_W23_CONSTMUL_TRANSFER_SCREEN")


if __name__ == "__main__":
    main()
