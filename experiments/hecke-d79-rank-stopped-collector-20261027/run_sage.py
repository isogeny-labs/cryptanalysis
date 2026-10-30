"""Live source lifts, incremental relation insertion, and rank-39 stop."""
import hashlib
import importlib.util
import json
import math
import resource
import sys
import time
from pathlib import Path

from sage.all import GF, classical_modular_polynomial, matrix, vector

from incremental import PairIndex, RankBasis, sparse

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
PLAN = json.loads((HERE / "inputs.json").read_text())
POST = json.loads((HERE / "post-selection.json").read_text())
SEAL = json.loads((HERE / "pre-run.json").read_text())


def pinned(item):
    path = ROOT / item["path"]
    assert hashlib.sha256(path.read_bytes()).hexdigest() == item["sha256"], str(path)
    return path


def module(item, name):
    spec = importlib.util.spec_from_file_location(name, pinned(item))
    out = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(out)
    return out


def save(out):
    (HERE / "result.json").write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")


def anchor_logs(cell, frozen, sage_points, baseline):
    q = frozen["q"]
    curve_order = frozen["class"]["curve_order"]
    field = GF(q)
    projected = [(curve_order // q) * point for point in sage_points]
    zero = sage_points[0].curve()(0)
    anchor = next(i for i, point in enumerate(projected) if point != zero)
    anchor_point = projected[anchor]
    assert int(anchor_point.order()) == q
    rows = baseline + [sparse(x["row"]) for x in cell["relation_rows"]]
    A = matrix(field, len(rows), 40, lambda i, j: rows[i].get(j, 0))
    assert int(A.rank()) == 39
    anchor_row = matrix(field, 1, 40, lambda _, j: int(j == anchor))
    assert int(A.stack(anchor_row).rank()) == 40
    rhs = vector(field, [0] * A.nrows() + [1])
    logs = [int(x) for x in A.stack(anchor_row).solve_right(rhs)]
    assert all(log * anchor_point == point for log, point in zip(logs, projected))
    return {"anchor_index": anchor, "anchor_point": [int(anchor_point[0]), int(anchor_point[1])],
            "anchored_logs": logs, "anchored_log_replay": "PASS"}


def main():
    assert hashlib.sha256((HERE / "selection.json").read_bytes()).hexdigest() == POST["selection_sha256"]
    assert hashlib.sha256((HERE / "incremental.py").read_bytes()).hexdigest() == SEAL["incremental_sha256"]
    selection = json.loads((HERE / "selection.json").read_text())
    assert selection["status"] == "CLASSES_FROZEN" and len(selection["selected"]) == PLAN["target_ready_classes"]
    control_gate = json.loads(pinned(PLAN["control_gate_result"]).read_text())
    control = next(x for x in control_gate["selected"] if x["p"] == PLAN["control_p"])
    f = PLAN["frozen"]
    H = module(f["hecke_source"], "stopped_hecke")
    P = module(f["prefix_runner"], "stopped_prefix")
    R = module(f["relation_helpers"], "stopped_relations")
    S = module(f["shared_build"], "stopped_build")
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
    funcs = {**funcs25, **funcs13}
    modpoly = classical_modular_polynomial(13)
    cases = [("known_success_control", control)] + [("fresh_panel", x) for x in selection["selected"]]
    out = {"schema": "hecke-d79-rank-stopped-collector-result-v1", "status": "RUNNING",
           "cache": cache_receipt, "cases": [], "rank_goal": PLAN["rank_goal"],
           "candidate_id": None, "target_online_ms": None}
    save(out)
    for cohort, frozen in cases:
        p, q = frozen["p"], frozen["q"]
        cell = {"cohort": cohort, "p": p, "q": q, "status": "RUNNING",
                "rank_goal_status": "UNKNOWN", "source_entries": [], "relation_rows": [],
                "source_steps": [], "candidate_id": None, "target_online_ms": None}
        out["cases"].append(cell)
        save(out)
        try:
            model = H.Reduced(p, funcs, jfun13, [2, 5, 13])
            assert int(model.E.cardinality()) == frozen["class"]["curve_order"]
            sage_points = [model.E(x, y) for x, y in frozen["class"]["class_points"]]
            points = [tuple(x) for x in frozen["class"]["class_points"]]
            neg, add = R.group_law(p)
            baseline = [sparse(x["row"]) for x in frozen["class"]["base_rows"] + frozen["direct_candidates"]]
            basis = RankBasis(q, baseline)
            assert basis.rank == frozen["baseline_rank_mod_q"] == R.rank(baseline, q)
            cell["baseline_rank_mod_q"] = basis.rank
            index = PairIndex(points, neg, add)
            cache = {}
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
                cell["source_entries"].append(entry)
                if entry["status"] != "OUTSIDE_CLASS_TRACE":
                    cell.update({"status": "CENSORED_SOURCE", "stop_source_count": k + 1,
                                 "collector_wall_ns": time.perf_counter_ns() - collector_start})
                    save(out)
                    break
                t0 = time.perf_counter_ns()
                new_rows, index_metrics = index.append(entry)
                index_ns = time.perf_counter_ns() - t0
                t0 = time.perf_counter_ns()
                novel = sum(basis.insert(sparse(row["row"])) for row in new_rows)
                rank_ns = time.perf_counter_ns() - t0
                cell["relation_rows"] = index.rows
                cell["source_steps"].append({"source": k, "source_count": k + 1,
                                             "lift_wall_ns": lift_ns, "index_wall_ns": index_ns,
                                             "rank_wall_ns": rank_ns, "new_rows": len(new_rows),
                                             "novel_rows": novel, "rank_mod_q": basis.rank,
                                             **index_metrics})
                save(out)
                if basis.rank >= PLAN["rank_goal"]:
                    cell.update({"status": "RANK_GOAL_REACHED", "rank_goal_status": "ACHIEVED",
                                 "stop_source_count": k + 1,
                                 "collector_wall_ns": time.perf_counter_ns() - collector_start})
                    break
            else:
                cell.update({"status": "FULL_POOL_BELOW_RANK_GOAL", "rank_goal_status": "BOUNDED_BELOW_GOAL",
                             "stop_source_count": 40, "collector_wall_ns": time.perf_counter_ns() - collector_start})
            if cell["status"] == "RANK_GOAL_REACHED":
                t0 = time.perf_counter_ns()
                cell.update(anchor_logs(cell, frozen, sage_points, baseline))
                cell["anchor_replay_wall_ns"] = time.perf_counter_ns() - t0
            cell["final_rank_mod_q"] = basis.rank
            cell["verified_relation_count"] = len(index.rows)
            cell["lift_sum_ns"] = sum(x["lift_wall_ns"] for x in cell["source_steps"])
            cell["index_sum_ns"] = sum(x["index_wall_ns"] for x in cell["source_steps"])
            cell["rank_sum_ns"] = sum(x["rank_wall_ns"] for x in cell["source_steps"])
            cell["peak_rss_bytes"] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        except Exception as exc:
            cell.update({"status": "SOURCE_OR_ANALYSIS_EXCEPTION", "rank_goal_status": "UNKNOWN",
                         "error_type": type(exc).__name__, "error": str(exc)[:300]})
        save(out)
        print(json.dumps({"cohort": cohort, "p": p, "status": cell["status"],
                          "sources": cell.get("stop_source_count"), "rank": cell.get("final_rank_mod_q")}), flush=True)
    out["status"] = "COMPLETE" if all(x["rank_goal_status"] != "UNKNOWN" for x in out["cases"]) else "COMPLETE_WITH_UNKNOWN"
    save(out)


if __name__ == "__main__":
    main()
