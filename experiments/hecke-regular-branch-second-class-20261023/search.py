"""Bounded, frozen search for another D1407/f6 regular-branch class."""
import hashlib
import json
from pathlib import Path

from sage.all import EllipticCurve_from_j, GF, is_prime

HERE = Path(__file__).resolve().parent


def main():
    raw = (HERE / "search_protocol.json").read_bytes()
    protocol = json.loads(raw)
    assert protocol["status"] == "FROZEN_BEFORE_SEARCH"
    assert protocol["family"] == {
        "DK": -1407, "f": 6, "v_min": 11, "v_max": 5000,
        "p_formula": "p=v*v+12663", "u_formula": "u=2*v",
    }
    rows, hit = [], None
    for v in range(11, 5001):
        p = v * v + 12663
        if not is_prime(p):
            continue
        u = 2 * v
        assert u * u - 4 * p == -1407 * 6 * 6
        model = EllipticCurve_from_j(GF(p)(-121))
        trace = int(model.trace_of_frobenius())
        row = {"v": v, "p": p, "u": u, "regular_j_trace": trace,
               "trace_matches": abs(trace) == u}
        if row["trace_matches"]:
            conductor = int(model.endomorphism_order().conductor())
            row["regular_j_conductor"] = conductor
            row["eligible"] = 6 % conductor == 0
            if row["eligible"]:
                hit = row
        rows.append(row)
        if hit:
            break
    result = {"status": "ELIGIBLE_PRIME_FOUND" if hit else "BOUNDED_SEARCH_EXHAUSTED",
              "protocol_sha256": hashlib.sha256(raw).hexdigest(),
              "prime_cases_tested": len(rows), "last_v": rows[-1]["v"] if rows else None,
              "hit": hit, "rows": rows}
    (HERE / "search_result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({k: v for k, v in result.items() if k != "rows"}, sort_keys=True))


if __name__ == "__main__":
    main()
