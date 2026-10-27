"""Rank-stopped collector with append-only compact per-class checkpoints."""
import hashlib
import importlib.util
import json
import math
import os
import resource
import sys
import time
from pathlib import Path

from sage.all import GF, classical_modular_polynomial, matrix, vector

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
PLAN = json.loads((HERE / "inputs.json").read_text())
POST = json.loads((HERE / "post-selection.json").read_text())
SEAL = json.loads((HERE / "pre-run.json").read_text())
CASES = HERE / "cases"


def pinned(item):
    path = ROOT / item["path"]
    assert hashlib.sha256(path.read_bytes()).hexdigest() == item["sha256"], str(path)
    return path


def module(item, name):
    spec = importlib.util.spec_from_file_location(name, pinned(item))
    out = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(out)
    return out


def write_json(path, value):
    path.write_text(json.dumps(value, separators=(",", ":"), sort_keys=True) + "\n")


def anchor_logs(frozen, sage_points, rows, sparse):
    q = frozen["q"]
    n = frozen["class"]["curve_order"]
    field = GF(q)
    projected = [(n // q) * point for point in sage_points]
    zero = sage_points[0].curve()(0)
    anchor = next(i for i, point in enumerate(projected) if point != zero)
    T = projected[anchor]
    assert int(T.order()) == q
    A = matrix(field, len(rows), 40, lambda i, j: rows[i].get(j, 0))
    assert int(A.rank()) == 39
    extra = matrix(field, 1, 40, lambda _, j: int(j == anchor))
    assert int(A.stack(extra).rank()) == 40
    rhs = vector(field, [0] * A.nrows() + [1])
    logs = [int(x) for x in A.stack(extra).solve_right(rhs)]
    assert all(log*T == point for log, point in zip(logs, projected))
    return {"anchor_index": anchor, "anchor_point": [int(T[0]), int(T[1])],
            "anchored_logs": logs, "anchored_log_replay": "PASS"}


def main():
    assert hashlib.sha256((HERE / "selection.json").read_bytes()).hexdigest() == POST["selection_sha256"]
    assert hashlib.sha256((HERE / "inputs.json").read_bytes()).hexdigest() == SEAL["inputs_sha256"]
    selection = json.loads((HERE / "selection.json").read_text())
    assert selection["status"] == "CLASSES_FROZEN" and len(selection["selected"]) == PLAN["target_ready_classes"]
    gate = json.loads(pinned(PLAN["control_gate_result"]).read_text())
    control = next(x for x in gate["selected"] if x["p"] == PLAN["control_p"])
    I = module(PLAN["incremental_module"], "compact_incremental")
    f = PLAN["frozen"]
    H = module(f["hecke_source"], "compact_hecke")
    P = module(f["prefix_runner"], "compact_prefix")
    R = module(f["relation_helpers"], "compact_relations")
    S = module(f["shared_build"], "compact_build")
    cache_path = pinned(f["cache_artifact"])
    sys.path.insert(0, str(pinned(f["cache_api"]).parent))
    from cache_api import resolve
    funcs25, jfun25 = H.build([2, 5])
    def forbidden_build(*args, **kwargs):
        raise RuntimeError("DEGREE13_BUILD_FORBIDDEN")
    H.build = forbidden_build
    funcs13, jfun13, cache_receipt = resolve(
        H, cache_path, f["cache_artifact"]["sha256"], f["hecke_source"]["sha256"],
        PLAN["cache_function_digest"], S.build_digest, "strict")
    assert jfun13 == jfun25 and not (set(funcs25) & set(funcs13))
    functions = {**funcs25, **funcs13}
    modpoly = classical_modular_polynomial(13)
    CASES.mkdir(exist_ok=False)
    cases = [("known_success_control", control)] + [("fresh_panel", x) for x in selection["selected"]]
    index = {"schema": "hecke-d79-compact-checkpoints-index-v1", "status": "RUNNING",
             "cache": cache_receipt, "cases": [], "candidate_id": None, "target_online_ms": None}
    write_json(HERE / "index.json", index)
    for cohort, frozen in cases:
        p, q = frozen["p"], frozen["q"]
        case_path = CASES / f"p{p}.jsonl"
        summary_path = CASES / f"p{p}-summary.json"
        assert not case_path.exists() and not summary_path.exists()
        summary = {"cohort": cohort, "p": p, "q": q, "status": "RUNNING",
                   "rank_goal_status": "UNKNOWN", "candidate_id": None, "target_online_ms": None}
        phase_times = []
        entries = []
        emitted = []
        collector_start = None
        try:
            model = H.Reduced(p, functions, jfun13, [2, 5, 13])
            assert int(model.E.cardinality()) == frozen["class"]["curve_order"]
            sage_points = [model.E(x, y) for x, y in frozen["class"]["class_points"]]
            points = [tuple(x) for x in frozen["class"]["class_points"]]
            neg, add = R.group_law(p)
            baseline = [I.sparse(x["row"]) for x in frozen["class"]["base_rows"] + frozen["direct_candidates"]]
            basis = I.RankBasis(q, baseline)
            assert basis.rank == frozen["baseline_rank_mod_q"] == R.rank(baseline, q)
            summary["baseline_rank_mod_q"] = basis.rank
            pair_index = I.PairIndex(points, neg, add)
            cache = {}
            with case_path.open("x", encoding="utf-8") as journal:
                collector_start = time.perf_counter_ns()
                for k, point in enumerate(sage_points):
                    t0 = time.perf_counter_ns()
                    poly = model.neighbour_x(13, point)
                    pattern = [[int(factor.degree()), int(mult)] for factor, mult in poly.factor()]
                    degree = math.lcm(*(d for d, _ in pattern))
                    if degree > 12 or any(mult != 1 for _, mult in pattern):
                        entry = {"source": k, "factor_pattern": pattern, "splitting_degree": degree,
                                 "status": "CENSORED_EXTENSION_OR_MULTIPLICITY"}
                    else:
                        entry, _ = P.lift_source(k, point, model, jfun13, sage_points, {}, cache, modpoly, pattern)
                    lift_ns = time.perf_counter_ns() - t0
                    entry["lift_wall_ns"] = lift_ns
                    entries.append(entry)
                    new_rows = []
                    index_ns = rank_ns = 0
                    index_metrics = {"pair_insertions": 0, "bucket_probes": 0, "new_verified_rows": 0}
                    novel = 0
                    if entry["status"] == "OUTSIDE_CLASS_TRACE":
                        t0 = time.perf_counter_ns()
                        new_rows, index_metrics = pair_index.append(entry)
                        index_ns = time.perf_counter_ns() - t0
                        t0 = time.perf_counter_ns()
                        novel = sum(basis.insert(I.sparse(row["row"])) for row in new_rows)
                        rank_ns = time.perf_counter_ns() - t0
                        emitted.extend(new_rows)
                    record = {"source": k, "entry": entry, "new_rows": new_rows,
                              "rank_mod_q": basis.rank, "novel_rows": novel,
                              "lift_wall_ns": lift_ns, "index_wall_ns": index_ns,
                              "rank_wall_ns": rank_ns, **index_metrics}
                    t0 = time.perf_counter_ns()
                    journal.write(json.dumps(record, separators=(",", ":"), sort_keys=True) + "\n")
                    journal.flush()
                    os.fsync(journal.fileno())
                    checkpoint_ns = time.perf_counter_ns() - t0
                    phase_times.append({"source": k, "checkpoint_wall_ns": checkpoint_ns})
                    if entry["status"] != "OUTSIDE_CLASS_TRACE":
                        summary.update({"status": "CENSORED_SOURCE", "rank_goal_status": "UNKNOWN"})
                        break
                    if basis.rank >= PLAN["rank_goal"]:
                        summary.update({"status": "RANK_GOAL_REACHED", "rank_goal_status": "ACHIEVED"})
                        break
                else:
                    summary.update({"status": "FULL_POOL_BELOW_RANK_GOAL", "rank_goal_status": "BOUNDED_BELOW_GOAL"})
                summary["collector_wall_ns"] = time.perf_counter_ns() - collector_start
            summary["source_count"] = len(entries)
            summary["final_rank_mod_q"] = basis.rank
            summary["verified_relation_count"] = len(emitted)
            summary["lift_sum_ns"] = sum(x["lift_wall_ns"] for x in entries)
            summary["index_sum_ns"] = sum(x["index_wall_ns"] for x in records_from_file(case_path))
            summary["rank_sum_ns"] = sum(x["rank_wall_ns"] for x in records_from_file(case_path))
            summary["checkpoint_sum_ns"] = sum(x["checkpoint_wall_ns"] for x in phase_times)
            summary["loop_overhead_ns"] = (summary["collector_wall_ns"] - summary["lift_sum_ns"]
                                           - summary["index_sum_ns"] - summary["rank_sum_ns"]
                                           - summary["checkpoint_sum_ns"])
            assert summary["loop_overhead_ns"] >= 0
            summary["checkpoint_phase_times"] = phase_times
            if summary["status"] == "RANK_GOAL_REACHED":
                t0 = time.perf_counter_ns()
                rows = baseline + [I.sparse(x["row"]) for x in emitted]
                summary.update(anchor_logs(frozen, sage_points, rows, I.sparse))
                summary["anchor_replay_wall_ns"] = time.perf_counter_ns() - t0
            summary["peak_rss_bytes"] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        except Exception as exc:
            summary.update({"status": "SOURCE_OR_ANALYSIS_EXCEPTION", "rank_goal_status": "UNKNOWN",
                            "error_type": type(exc).__name__, "error": str(exc)[:300],
                            "source_count": len(entries)})
            if collector_start is not None and "collector_wall_ns" not in summary:
                summary["collector_wall_ns"] = time.perf_counter_ns() - collector_start
        write_json(summary_path, summary)
        item = {"cohort": cohort, "p": p, "q": q, "status": summary["status"],
                "rank_goal_status": summary["rank_goal_status"], "source_count": summary["source_count"],
                "journal": str(case_path.relative_to(HERE)),
                "journal_sha256": hashlib.sha256(case_path.read_bytes()).hexdigest(),
                "summary": str(summary_path.relative_to(HERE)),
                "summary_sha256": hashlib.sha256(summary_path.read_bytes()).hexdigest()}
        index["cases"].append(item)
        write_json(HERE / "index.json", index)
        print(json.dumps({"cohort": cohort, "p": p, "status": summary["status"],
                          "sources": summary["source_count"], "rank": summary.get("final_rank_mod_q")}), flush=True)
    index["status"] = "COMPLETE" if all(x["rank_goal_status"] != "UNKNOWN" for x in index["cases"]) else "COMPLETE_WITH_UNKNOWN"
    write_json(HERE / "index.json", index)


def records_from_file(path):
    return [json.loads(line) for line in path.read_text().splitlines() if line]


if __name__ == "__main__":
    main()
