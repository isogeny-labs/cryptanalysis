"""Replay full and opposite-sign triple caches on audited sources."""
import hashlib
import importlib.util
import json
import os
import resource
import sys
import time
from pathlib import Path

from sage.all import GF, matrix, vector
from symmetric_index import SymmetricTripleSumEightIndex

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
PLAN = json.loads((HERE / "inputs.json").read_text())
SEAL = json.loads((HERE / "pre-run.json").read_text())

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def pinned(item):
    path = ROOT / item["path"]
    assert sha(path) == item["sha256"], path
    return path

def module(item, name):
    spec = importlib.util.spec_from_file_location(name, pinned(item))
    out = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(out)
    return out

def save(path, value):
    path.write_text(json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n")

def digest_rows(rows):
    return hashlib.sha256(json.dumps(rows, sort_keys=True, separators=(",", ":")).encode()).hexdigest()

class GroupCounter:
    def __init__(self, neg, add):
        self.raw_neg, self.raw_add = neg, add
        self.neg_calls = self.add_calls = 0
    def neg(self, point):
        self.neg_calls += 1
        return self.raw_neg(point)
    def add(self, left, right):
        self.add_calls += 1
        return self.raw_add(left, right)

def cache_bytes(cache):
    return sys.getsizeof(cache) + sum(sys.getsizeof(key) + sys.getsizeof(value)
                                       for key, value in cache.items())

def anchored_logs(q, n, points, rows):
    F = GF(q)
    projected = [(n // q)*point for point in points]
    zero = points[0].curve()(0)
    anchor = next(j for j, point in enumerate(projected) if point != zero)
    T = projected[anchor]
    assert int(T.order()) == q
    A = matrix(F, len(rows), 40, lambda i, j: rows[i].get(j, 0))
    assert int(A.rank()) == 39
    augmented = A.stack(matrix(F, 1, 40, lambda _, j: int(j == anchor)))
    logs = [int(x) for x in augmented.solve_right(vector(F, [0]*len(rows) + [1]))]
    assert all(log*T == point for log, point in zip(logs, projected))
    return {"anchor_index": anchor, "anchored_logs": logs, "anchored_log_replay": "PASS"}

def main():
    for name, field in (("inputs.json", "inputs_sha256"), ("PROTOCOL.md", "protocol_sha256"),
                        ("symmetric_index.py", "symmetric_index_sha256"),
                        ("sage-runtime-info.txt", "runtime_sha256"),
                        ("run_sage.py", "runner_sha256")):
        assert sha(HERE / name) == SEAL[field]
    source_selection = json.loads(pinned(PLAN["source_selection"]).read_text())
    source_index = json.loads(pinned(PLAN["source_index"]).read_text())
    source_audit = json.loads(pinned(PLAN["source_audit"]).read_text())
    pinned(PLAN["source_post_audit"])
    assert source_selection["status"] == source_index["status"] == "COMPLETE" or (source_selection["status"] == "CLASSES_FROZEN" and source_index["status"] == "COMPLETE")
    assert source_audit["status"] == "PASS" and len(source_index["cases"]) == 9
    I = module(PLAN["incremental_module"], "pair_kernel_rank")
    R = module(PLAN["relation_helpers"], "pair_kernel_group")
    B = module(PLAN["baseline_index"], "pair_kernel_baseline")
    source_root = pinned(PLAN["source_index"]).parent
    source_selection_dir = {x["p"]: x for x in source_selection["selected"]}
    control_selection = json.loads((source_root.parent / "hecke-d79-live-eight-20261027" / "selection.json").read_text())
    source_selection_dir[2076797] = next(x for x in control_selection["selected"] if x["p"] == 2076797)
    case_dir = HERE / "cases"
    case_dir.mkdir(exist_ok=False)
    index = {"schema": "hecke-d79-sign-symmetry-index-v1", "status": "RUNNING",
             "candidate_id": None, "target_online_ms": None, "cases": []}
    save(HERE / "index.json", index)
    for case_number, item in enumerate(source_index["cases"]):
        p, q = item["p"], item["q"]
        frozen = source_selection_dir[p]
        journal_path = source_root / item["journal"]
        assert sha(journal_path) == item["journal_sha256"]
        prior = [json.loads(line) for line in journal_path.read_text().splitlines()]
        prior_summary_path = source_root / item["summary"]
        assert sha(prior_summary_path) == item["summary_sha256"]
        prior_summary = json.loads(prior_summary_path.read_text())
        points = [tuple(x) for x in frozen["class"]["class_points"]]
        sage_points = [__import__("sage.all", fromlist=["EllipticCurve"]).EllipticCurve(GF(p), [0,-1,1,-10,-20])(x,y) for x,y in points]
        raw_neg, raw_add = R.group_law(p)
        baseline = [I.sparse(x["row"]) for x in frozen["class"]["base_rows"] + frozen["direct_candidates"]]
        arm_order = ("triple_sum", "symmetric") if case_number % 2 == 0 else ("symmetric", "triple_sum")
        arms = {}
        for arm in arm_order:
            basis = I.RankBasis(q, baseline)
            counter = GroupCounter(raw_neg, raw_add)
            cls = B.TripleSumEightIndex if arm == "triple_sum" else SymmetricTripleSumEightIndex
            index_arm = cls(points, counter.neg, counter.add, PLAN["support_eight_row_cap"],
                PLAN["support_eight_wall_cap_seconds"], PLAN["support_eight_probe_cap"],
                basis, PLAN["rank_goal"], "reverse_lex")
            arms[arm] = {"basis": basis, "counter": counter, "index": index_arm,
                         "rows": list(baseline), "first": None, "last_metrics": None,
                         "source_wall_ns": 0}
        rows_path = case_dir / f"p{p}.jsonl"
        summary_path = case_dir / f"p{p}-summary.json"
        case_status = "COMPLETE"
        with rows_path.open("x") as out:
            for k, record in enumerate(prior):
                assert record["source"] == k and record["entry"]["status"] == "OUTSIDE_CLASS_TRACE"
                lower = [I.sparse(row["row"]) for name in ("four", "five", "six", "seven") for row in record["rows"][name]]
                for arm in arm_order:
                    a = arms[arm]
                    for row in lower:
                        a["basis"].insert(row)
                        a["rows"].append(row)
                row_out = {"source": k, "lower_rows_sha256": digest_rows({name: record["rows"][name] for name in ("four", "five", "six", "seven")}),
                           "arm_order": arm_order, "arms": {}}
                for arm in arm_order:
                    a = arms[arm]
                    before_add, before_neg = a["counter"].add_calls, a["counter"].neg_calls
                    if a["first"] is not None:
                        rows, metrics, elapsed = [], {"status": "SKIPPED_RANK_GOAL", "step_probes": 0}, 0
                    elif a["basis"].rank >= PLAN["rank_goal"]:
                        a["first"] = k + 1
                        rows, metrics, elapsed = [], {"status": "SKIPPED_LOWER_RANK_GOAL", "step_probes": 0}, 0
                    else:
                        t0 = time.perf_counter_ns()
                        rows, metrics = a["index"].append(record["entry"])
                        elapsed = time.perf_counter_ns() - t0
                        a["rows"].extend(I.sparse(row["row"]) for row in rows)
                        if metrics["status"] == "RANK_GOAL_REACHED":
                            a["first"] = k + 1
                        elif metrics["status"] != "COMPLETE":
                            case_status = metrics["status"]
                    a["source_wall_ns"] += elapsed
                    expected_rows = record["rows"]["reverse_lex_eight"]
                    expected_metrics = record["eight_metrics"]["reverse_lex"]
                    assert digest_rows(rows) == digest_rows(expected_rows)
                    assert metrics["step_probes"] == expected_metrics["step_probes"]
                    assert metrics["status"] == expected_metrics["status"]
                    assert a["basis"].rank == record["rank_eight_mod_q"]["reverse_lex"]
                    row_out["arms"][arm] = {"row_sha256": digest_rows(rows),
                        "status": metrics["status"], "rank": a["basis"].rank,
                        "step_probes": metrics["step_probes"], "step_matches": metrics.get("matches", 0),
                        "pair_insertions": metrics.get("pair_insertions", 0),
                        "triple_cache_insertions": metrics.get("triple_cache_insertions", 0),
                        "pair_cache_entries": metrics.get("pair_cache_entries", len(a["index"].pair_sums)),
                        "triple_cache_entries": metrics.get("triple_cache_entries", len(getattr(a["index"], "triple_sums", {}))),
                        "triple_insertions": metrics.get("triple_insertions", 0),
                        "add_calls": a["counter"].add_calls - before_add,
                        "neg_calls": a["counter"].neg_calls - before_neg,
                        "wall_ns": elapsed}
                out.write(json.dumps(row_out, sort_keys=True, separators=(",", ":")) + "\n")
                out.flush(); os.fsync(out.fileno())
                if case_status != "COMPLETE":
                    break
                if all(arms[arm]["first"] is not None for arm in arm_order):
                    break
        summary = {"cohort": item["cohort"], "p": p, "q": q, "status": case_status,
                   "arm_order": arm_order, "source_count": k + 1, "candidate_id": None,
                   "process_peak_rss_bytes": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                   "target_online_ms": None, "arms": {}}
        logged = [json.loads(line) for line in rows_path.read_text().splitlines()]
        for arm in arm_order:
            a = arms[arm]
            replay = None
            if a["first"] is not None:
                replay = anchored_logs(q, frozen["class"]["curve_order"], sage_points, a["rows"])
                assert replay["anchored_logs"] == prior_summary["eight_replay"]["reverse_lex"]["anchored_logs"]
            summary["arms"][arm] = {"first_rank39_source_count": a["first"],
                "final_rank": a["basis"].rank, "probes": a["index"].probes,
                "matches": len(a["index"].rows),
                "add_calls": a["counter"].add_calls, "neg_calls": a["counter"].neg_calls,
                "component_wall_ns": a["source_wall_ns"], "anchored_replay": replay,
                "pair_cache_entries": len(a["index"].pair_sums),
                "triple_cache_entries": len(getattr(a["index"], "triple_sums", {})),
                "cache_shallow_bytes": cache_bytes(a["index"].pair_sums) +
                    cache_bytes(getattr(a["index"], "triple_sums", {}))}
            assert summary["arms"][arm]["add_calls"] == sum(x["arms"][arm]["add_calls"] for x in logged)
            assert summary["arms"][arm]["neg_calls"] == sum(x["arms"][arm]["neg_calls"] for x in logged)
            assert summary["arms"][arm]["component_wall_ns"] == sum(x["arms"][arm]["wall_ns"] for x in logged)
        assert summary["arms"]["triple_sum"]["probes"] == summary["arms"]["symmetric"]["probes"]
        assert summary["arms"]["triple_sum"]["first_rank39_source_count"] == summary["arms"]["symmetric"]["first_rank39_source_count"]
        save(summary_path, summary)
        index["cases"].append({"cohort": item["cohort"], "p": p, "q": q, "status": case_status,
            "journal": rows_path.relative_to(HERE).as_posix(), "journal_sha256": sha(rows_path),
            "summary": summary_path.relative_to(HERE).as_posix(), "summary_sha256": sha(summary_path),
            "triple_sum_add_calls": summary["arms"]["triple_sum"]["add_calls"],
            "symmetric_add_calls": summary["arms"]["symmetric"]["add_calls"],
            "probes": summary["arms"]["triple_sum"]["probes"]})
        save(HERE / "index.json", index)
        print(json.dumps(index["cases"][-1], sort_keys=True), flush=True)
    index["status"] = "COMPLETE" if len(index["cases"]) == 9 and all(x["status"] == "COMPLETE" for x in index["cases"]) else "CENSORED"
    save(HERE / "index.json", index)

if __name__ == "__main__":
    main()
