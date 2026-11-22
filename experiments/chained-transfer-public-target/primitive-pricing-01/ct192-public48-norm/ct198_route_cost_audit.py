#!/usr/bin/env python3
"""CT198: exact, frozen-source 48-packet route-counter audit, NOT timing or PCC."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import source_contract as original

ARMS = ("direct_composite", "literal_sequential_Jacobian_maps",
        "strongest_retained_lift_chain")
FIELDS = tuple(sorted(original.COUNTERS))
C13 = "degree13_elliptic_evaluation"
C169 = "degree169_elliptic_evaluation"
N2 = "transported_norm_doubling"

class CounterAuditError(ValueError):
    pass

def require(ok, why):
    if not ok:
        raise CounterAuditError(why)

def vector_diff(x, y):
    """Subtract two exact, non-negative integer counter dictionaries."""
    return {name: x[name] - y[name] for name in FIELDS}

def audit_rows(rows):
    """Audit exact frozen 48 rows; caller must also pin fixture bytes externally."""
    require(type(rows) is list and len(rows) == 48, "requires 48 source rows")
    seen = set()
    totals = {arm: {name: 0 for name in FIELDS} for arm in ARMS}
    groups = {name: {arm: {k: 0 for k in FIELDS} for arm in ARMS}
              for name in ("identity", "generic")}
    class_counts = {"identity": 0, "generic": 0}
    for index, row in enumerate(rows):
        require(type(row) is dict and set(row) == original.ROW_FIELDS,
                f"row {index}: original row schema mismatch")
        key = (row["from"], row["to"], row["sector"], row["scalar_OUTSIDE_runtime"])
        require(all(type(v) is int for v in key), f"row {index}: invalid cohort")
        require(key not in seen, f"row {index}: repeated cohort")
        seen.add(key)
        group = "identity" if key[3] == 0 else "generic"
        class_counts[group] += 1
        for arm in ARMS:
            counts = row[arm]
            require(type(counts) is dict and counts.keys() == original.COUNTERS,
                    f"row {index} {arm}: counter fields changed")
            for name in FIELDS:
                v = counts[name]
                require(type(v) is int and 0 <= v < 2**64,
                        f"row {index} {arm}: invalid nonnegative count for {name}")
                totals[arm][name] += v
                groups[group][arm][name] += v
        direct = row[ARMS[0]]
        sequential = row[ARMS[1]]
        retained = row[ARMS[2]]
        require((direct[C169], direct[C13], retained[C169], retained[C13])
                == (1, 0, 0, 2),
                f"row {index}: C169/C13 route swap not exact")
        require(direct[N2] == retained[N2] == 1,
                f"row {index}: norm reuse does NOT distinguish direct/retained")
        require(all(direct[name] == retained[name] for name in FIELDS
                    if name not in (C13, C169)),
                f"row {index}: hidden non-isogeny counter difference")
        require((sequential[C169], sequential[C13], sequential[N2])
                == (0, 2, 2), f"row {index}: sequential route counters changed")
        require(all(sequential[name] >= retained[name] for name in FIELDS),
                f"row {index}: sequential no longer dominates retained in count vector")
        require(sequential[N2] - retained[N2] == 1,
                f"row {index}: lost exactly one reused transported norm")
    expected = {(a, b, sector, scalar)
                for a, b in ((0, 2), (2, 0))
                for sector in range(4)
                for scalar in original.SCALARS}
    require(seen == expected and class_counts == {"identity": 8, "generic": 40},
            "missing/duplicate frozen cohort or identity case")
    return {
        "schema": "ct198-frozen48-counter-cost-crossover/v1",
        "standing": "[pcc:unverified]",
        "basis": "source-frozen CT125 48-packet counter vectors, not native timing",
        "source_git_blob": original.ORIGINAL_BLOB,
        "fixture_git_blob": original.FROZEN_BLOB,
        "packets": 48,
        "class_counts": class_counts,
        "per_route_total_48": totals,
        "per_class_total": groups,
        "retained_minus_direct_48": vector_diff(totals[ARMS[2]], totals[ARMS[0]]),
        "sequential_minus_retained_48": vector_diff(totals[ARMS[1]], totals[ARMS[2]]),
        "cost_identity_per_packet": "retained_minus_direct=C13a+C13b-C169; norm cancels",
        "route_wall_time_measured": False,
        "complete_single_target_ecdlp_solved": False,
        "independent_pcc": False,
    }

def audited_original():
    b = original.FROZEN.read_bytes()
    original.validate_fixture(b)
    require(original.blob(b) == original.FROZEN_BLOB,
            "original fixture Git-blob mismatch")
    doc = json.loads(b)
    return audit_rows(doc["all48"]), hashlib.sha256(b).hexdigest()

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report, digest = audited_original()
    report["fixture_sha256_producer_only"] = digest
    output = json.dumps(report, sort_keys=True, indent=2) + "\n"
    if args.output:
        args.output.write_text(output)
    else:
        print(output, end="")

if __name__ == "__main__":
    try:
        main()
    except (CounterAuditError, ValueError, OSError, KeyError, TypeError) as exc:
        raise SystemExit("CT198 REFUSED: " + str(exc)) from exc
