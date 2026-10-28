"""Independent custody, row, and group-call accounting for paired kernels."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
PLAN = json.loads((HERE / "inputs.json").read_text())
POST = json.loads((HERE / "post-run.json").read_text())

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def pinned(item):
    path = ROOT / item["path"]
    assert sha(path) == item["sha256"], path
    return path

def rows_sha(rows):
    return hashlib.sha256(json.dumps(rows, sort_keys=True, separators=(",", ":")).encode()).hexdigest()

def main():
    for name, digest in POST["sha256"].items():
        assert sha(HERE / name) == digest, name
    old_index = json.loads(pinned(PLAN["source_index"]).read_text())
    old_audit = json.loads(pinned(PLAN["source_audit"]).read_text())
    pinned(PLAN["source_selection"])
    pinned(PLAN["source_post_audit"])
    assert old_audit["status"] == "PASS" and len(old_audit["cases"]) == 9
    index = json.loads((HERE / "index.json").read_text())
    assert index["status"] == "COMPLETE" and len(index["cases"]) == 9
    source_root = pinned(PLAN["source_index"]).parent
    checked = []
    for prior_item, item in zip(old_index["cases"], index["cases"]):
        assert (item["cohort"], item["p"], item["q"]) == (prior_item["cohort"], prior_item["p"], prior_item["q"])
        jp, sp = HERE / item["journal"], HERE / item["summary"]
        assert sha(jp) == item["journal_sha256"] and sha(sp) == item["summary_sha256"]
        prior_jp, prior_sp = source_root / prior_item["journal"], source_root / prior_item["summary"]
        assert sha(prior_jp) == prior_item["journal_sha256"]
        assert sha(prior_sp) == prior_item["summary_sha256"]
        records = [json.loads(line) for line in jp.read_text().splitlines()]
        prior = [json.loads(line) for line in prior_jp.read_text().splitlines()]
        summary = json.loads(sp.read_text())
        prior_summary = json.loads(prior_sp.read_text())
        assert len(records) == summary["source_count"] <= len(prior)
        assert summary["status"] == item["status"] == "COMPLETE"
        for k, (record, old) in enumerate(zip(records, prior)):
            assert record["source"] == old["source"] == k
            assert record["lower_rows_sha256"] == rows_sha({name: old["rows"][name] for name in ("four", "five", "six", "seven")})
            assert tuple(record["arm_order"]) == tuple(summary["arm_order"])
            baseline = record["arms"]["baseline"]
            pair = record["arms"]["pair_sum"]
            expected_rows = old["rows"]["reverse_lex_eight"]
            expected_metrics = old["eight_metrics"]["reverse_lex"]
            for arm in (baseline, pair):
                assert arm["row_sha256"] == rows_sha(expected_rows)
                assert arm["status"] == expected_metrics["status"]
                assert arm["step_probes"] == expected_metrics["step_probes"]
                assert arm["rank"] == old["rank_eight_mod_q"]["reverse_lex"]
                assert arm["add_calls"] >= 0 and arm["neg_calls"] >= 0 and arm["wall_ns"] >= 0
            assert baseline["step_probes"] == pair["step_probes"]
            assert pair["pair_insertions"] == (4*k if pair["status"] == "COMPLETE" else 0)
            assert baseline["add_calls"] - pair["add_calls"] == 3*pair["step_probes"] - pair["pair_insertions"]
        for arm_name in ("baseline", "pair_sum"):
            arm = summary["arms"][arm_name]
            assert arm["first_rank39_source_count"] == prior_item["first_eight_source_count"]["reverse_lex"]
            assert arm["final_rank"] == 39
            assert arm["probes"] == prior_item["actual_eight_probes"]["reverse_lex"] == item["probes"]
            assert arm["add_calls"] == sum(x["arms"][arm_name]["add_calls"] for x in records)
            assert arm["neg_calls"] == sum(x["arms"][arm_name]["neg_calls"] for x in records)
            assert arm["component_wall_ns"] == sum(x["arms"][arm_name]["wall_ns"] for x in records)
            assert arm["anchored_replay"]["anchored_log_replay"] == "PASS"
            assert arm["anchored_replay"]["anchored_logs"] == prior_summary["eight_replay"]["reverse_lex"]["anchored_logs"]
        assert item["baseline_add_calls"] == summary["arms"]["baseline"]["add_calls"]
        assert item["pair_sum_add_calls"] == summary["arms"]["pair_sum"]["add_calls"]
        checked.append({"cohort": item["cohort"], "p": item["p"],
            "baseline_add_calls": item["baseline_add_calls"],
            "pair_sum_add_calls": item["pair_sum_add_calls"],
            "probes": item["probes"], "status": "PASS"})
        print(json.dumps(checked[-1], sort_keys=True), flush=True)
    fresh = [x for x in checked if x["cohort"] == "fresh"]
    assert len(fresh) == 8
    baseline_total = sum(x["baseline_add_calls"] for x in fresh)
    pair_total = sum(x["pair_sum_add_calls"] for x in fresh)
    result = {"schema": "hecke-d79-pair-sum-audit-v1", "status": "PASS", "cases": checked,
        "fresh_baseline_add_calls": baseline_total, "fresh_pair_sum_add_calls": pair_total,
        "fresh_add_reduction": baseline_total - pair_total,
        "fresh_add_reduction_fraction": (baseline_total-pair_total)/baseline_total,
        "candidate_id": None, "target_online_ms": None}
    (HERE / "audit.json").write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")

if __name__ == "__main__":
    main()
