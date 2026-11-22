"""Complete, disjoint cold-query accounting. Not an execution or math verifier.

Input is a prospective receipt adapter contract; historical timing data are
not silently converted. Missing phases, failed/censored rows and unit errors
reject the entire comparison. Scientific standing remains unverified.
"""
import argparse
import json
from pathlib import Path

PHASES = {"setup", "generator", "target_transport", "solve", "source_verify"}
IDENTITY = {"scope", "source_curve", "target_curve", "subgroup_order", "cohort_sha256", "host_receipt_sha256"}


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def uint(value, name):
    require(type(value) is int and value >= 0, f"{name}: nonnegative integer required")
    return value


def sha(value):
    return isinstance(value, str) and len(value) == 64 and all(c in "0123456789abcdef" for c in value)


def audit(panel):
    require(panel.get("schema") == "cold-transfer-cost/v1", "schema")
    identity = panel.get("identity", {})
    require(set(identity) == IDENTITY, "complete exact identity required")
    require(all(type(v) is str and v for v in identity.values()), "identity values")
    require(identity["subgroup_order"].isdigit() and int(identity["subgroup_order"]) > 1, "subgroup order")
    require(sha(identity["cohort_sha256"]) and sha(identity["host_receipt_sha256"]), "identity digest")
    require(panel.get("boundary") == "disjoint-cold-per-query", "amortized or nested boundary rejected")
    targets = panel.get("targets")
    require(isinstance(targets, list) and len(targets) >= 5, "at least five public targets")
    require(all(type(t) is str and t for t in targets), "public target identifiers")
    require(len(targets) == len(set(targets)), "duplicate public target")
    reps = uint(panel.get("repeats"), "repeats")
    require(reps >= 2, "at least two repetitions")
    arms = panel.get("arms", {})
    require(isinstance(arms, dict) and set(arms.values()) == {"source", "transferred"}, "both arm kinds required")
    require(all(type(a) is str and a for a in arms), "arm names")
    rows = panel.get("rows")
    require(isinstance(rows, list), "rows")
    expected = {(a, t, r) for a in arms for t in targets for r in range(reps)}
    observed, totals = set(), {a: 0 for a in arms}
    rss = {a: 0 for a in arms}
    for row in rows:
        key = (row.get("arm"), row.get("target"), row.get("repeat"))
        require(type(key[2]) is int and key in expected and key not in observed, "unexpected or duplicate row")
        observed.add(key)
        require(row.get("status") == "ok", "failed or censored row")
        require(row.get("unit") == "ns", "unit must be ns")
        phases = row.get("phases_ns", {})
        require(set(phases) == PHASES, "missing/extra phase; unknown is not zero")
        charged = sum(uint(v, name) for name, v in phases.items())
        total = uint(row.get("total_ns"), "total_ns")
        require(total > 0 and total == charged, "complete total must equal disjoint phase sum")
        memory = uint(row.get("peak_rss_bytes"), "peak_rss_bytes")
        require(memory > 0, "memory receipt missing")
        require(sha(row.get("source_sha256")) and sha(row.get("binary_sha256")), "source/binary digests")
        require(type(row.get("answer_check")) is str and row["answer_check"], "answer-check artifact missing")
        totals[key[0]] += total
        rss[key[0]] = max(rss[key[0]], memory)
    require(observed == expected, "incomplete panel")
    source = min((totals[a], a) for a in arms if arms[a] == "source")
    transferred = min((totals[a], a) for a in arms if arms[a] == "transferred")
    queries = len(targets) * reps
    return {"standing": "[pcc:unverified]", "identity": identity,
            "scope": "accounting only; arithmetic, execution, isolation and provenance not certified",
            "totals_ns": totals, "peak_rss_bytes": rss,
            "best_fixed_source": source, "best_fixed_transferred": transferred,
            "source_over_transferred": source[0] / transferred[0],
            "additional_headroom_ns_per_query": (source[0] - transferred[0]) / queries,
            "additional_headroom_ms_per_query": (source[0] - transferred[0]) / queries / 1_000_000}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("panel", type=Path)
    args = parser.parse_args()
    print(json.dumps(audit(json.loads(args.panel.read_text())), indent=2))
