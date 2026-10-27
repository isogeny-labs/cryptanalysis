"""Deterministic retrospective diagnostics for sealed D79 source journals."""
import hashlib
import json
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent / "hecke-d79-compact-checkpoints-20261027"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    index_path = SOURCE / "index.json"
    index = json.loads(index_path.read_text())
    assert index["status"] == "COMPLETE"
    cases = []
    for case in index["cases"]:
        p = case["p"]
        path = SOURCE / "cases" / f"p{p}.jsonl"
        rows = [json.loads(line) for line in path.read_text().splitlines()]
        summary_path = SOURCE / "cases" / f"p{p}-summary.json"
        assert path.relative_to(SOURCE).as_posix() == case["journal"]
        assert summary_path.relative_to(SOURCE).as_posix() == case["summary"]
        assert digest(path) == case["journal_sha256"]
        assert digest(summary_path) == case["summary_sha256"]
        summary = json.loads(summary_path.read_text())
        assert summary["p"] == p and summary["q"] == case["q"]
        assert len(rows) == summary["source_count"]
        assert [r["source"] for r in rows] == list(range(len(rows)))
        assert sum(len(r["new_rows"]) for r in rows) == summary["verified_relation_count"]
        assert sum(r["novel_rows"] for r in rows) == summary["final_rank_mod_q"] - summary["baseline_rank_mod_q"]
        traces = [tuple(t) for r in rows for t in r["entry"].get("outside_traces", [])]
        trace_counts = Counter(traces)
        relation_sources = Counter()
        for r in rows:
            for row in r["new_rows"]:
                for source in row["sources"]:
                    relation_sources[source] += 1
        result = {
            "p": p, "q": summary["q"], "cohort": summary["cohort"],
            "status": summary["status"], "source_count": len(rows),
            "baseline_rank": summary["baseline_rank_mod_q"],
            "final_rank": summary["final_rank_mod_q"],
            "rank_gain": summary["final_rank_mod_q"] - summary["baseline_rank_mod_q"],
            "verified_rows": summary["verified_relation_count"],
            "rows_dependent_mod_baseline": summary["verified_relation_count"] - sum(r["novel_rows"] for r in rows),
            "sources_with_rows": sum(bool(r["new_rows"]) for r in rows),
            "sources_with_rank_gain": sum(bool(r["novel_rows"]) for r in rows),
            "first_row_source": next((r["source"] for r in rows if r["new_rows"]), None),
            "first_rank_gain_source": next((r["source"] for r in rows if r["novel_rows"]), None),
            "outside_trace_incidences": len(traces),
            "distinct_outside_traces": len(trace_counts),
            "repeated_trace_incidences": len(traces) - len(trace_counts),
            "shared_trace_buckets": sum(c > 1 for c in trace_counts.values()),
            "largest_trace_bucket": max(trace_counts.values(), default=0),
            "relation_support_sources": len(relation_sources),
            "max_relation_incidence_per_source": max(relation_sources.values(), default=0),
            "row_count_by_emitting_source": [[r["source"], len(r["new_rows"]), r["novel_rows"]] for r in rows if r["new_rows"] or r["novel_rows"]],
            "journal_sha256": digest(path), "summary_sha256": digest(summary_path),
        }
        cases.append(result)
    out = {"schema": "hecke-d79-rank-bottleneck-v1", "input_index_sha256": digest(index_path),
           "candidate_id": None, "target_online_ms": None, "cases": cases}
    (HERE / "analysis.json").write_text(json.dumps(out, sort_keys=True, separators=(",", ":")) + "\n")
    for c in cases:
        print(c["p"], c["rank_gain"], c["verified_rows"], c["distinct_outside_traces"], c["repeated_trace_incidences"], c["first_rank_gain_source"])


if __name__ == "__main__":
    main()
