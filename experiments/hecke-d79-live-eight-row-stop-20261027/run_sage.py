"""Prospective live D79 row-level support-eight rank stop."""
import hashlib
import importlib.util
import json
import math
from math import comb
import os
import sys
import time
from pathlib import Path

from sage.all import GF, classical_modular_polynomial, matrix, vector

from wide_index import WideIndex
from rank_stop_index import RankStopEightIndex

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
PLAN = json.loads((HERE / "inputs.json").read_text())
POST = json.loads((HERE / "post-selection.json").read_text())
SEAL = json.loads((HERE / "pre-run.json").read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def pinned(item):
    path = ROOT / item["path"]
    assert sha(path) == item["sha256"], str(path)
    return path


def module(item, name):
    spec = importlib.util.spec_from_file_location(name, pinned(item))
    out = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(out)
    return out


def save(path, value):
    path.write_text(json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n")


def records(path):
    return [json.loads(line) for line in path.read_text().splitlines()]


def anchored_logs(q, n, sage_points, rows):
    F = GF(q)
    projected = [(n // q)*point for point in sage_points]
    zero = sage_points[0].curve()(0)
    anchor = next(j for j, point in enumerate(projected) if point != zero)
    T = projected[anchor]
    assert int(T.order()) == q
    A = matrix(F, len(rows), 40, lambda i, j: rows[i].get(j, 0))
    assert int(A.rank()) == 39
    augmented = A.stack(matrix(F, 1, 40, lambda _, j: int(j == anchor)))
    assert int(augmented.rank()) == 40
    logs = [int(x) for x in augmented.solve_right(vector(F, [0]*len(rows) + [1]))]
    assert all(log*T == point for log, point in zip(logs, projected))
    return {"anchor_index": anchor, "anchor_point": [int(T[0]), int(T[1])],
            "anchored_logs": logs, "anchored_log_replay": "PASS"}


def main():
    assert sha(HERE / "selection.json") == POST["selection_sha256"]
    assert sha(HERE / "inputs.json") == POST["inputs_sha256"]
    for name, field in (("preflight.json", "preflight_sha256"),
                        ("wide_index.py", "wide_index_sha256"),
                        ("rank_stop_index.py", "rank_stop_index_sha256"),
                        ("PROTOCOL.md", "protocol_sha256"),
                        ("sage-runtime-info.txt", "sage_runtime_info_sha256"),
                        ("run_sage.py", "runner_sha256")):
        assert sha(HERE / name) == SEAL[field]
    selection = json.loads((HERE / "selection.json").read_text())
    assert selection["status"] == "CLASSES_FROZEN"
    assert [x["p"] for x in selection["selected"]] == POST["selected_p"]
    prior_selection = json.loads(pinned(PLAN["preflight_support_eight_selection"]).read_text())
    control = next(x for x in prior_selection["selected"] if x["p"] == PLAN["control_p"])
    I = module(PLAN["incremental_module"], "live_seven_four")
    Five = module(PLAN["frozen_five_index"], "live_seven_five")
    f = PLAN["frozen"]
    H = module(f["hecke_source"], "live_seven_hecke")
    P = module(f["prefix_runner"], "live_seven_prefix")
    R = module(f["relation_helpers"], "live_seven_group")
    S = module(f["shared_build"], "live_seven_build")
    cache_path = pinned(f["cache_artifact"])
    sys.path.insert(0, str(pinned(f["cache_api"]).parent))
    from cache_api import resolve
    funcs25, jfun25 = H.build([2, 5])
    def forbidden_build(*args, **kwargs):
        raise RuntimeError("DEGREE13_BUILD_FORBIDDEN")
    H.build = forbidden_build
    funcs13, jfun13, receipt = resolve(H, cache_path, f["cache_artifact"]["sha256"],
                                       f["hecke_source"]["sha256"],
                                       PLAN["cache_function_digest"], S.build_digest, "strict")
    assert jfun13 == jfun25 and not (set(funcs25) & set(funcs13))
    functions = {**funcs25, **funcs13}
    modpoly = classical_modular_polynomial(13)
    case_dir = HERE / "cases"
    case_dir.mkdir(exist_ok=False)
    cases = [("known_control", control)] + [("fresh", x) for x in selection["selected"]]
    index = {"schema": "hecke-d79-live-eight-row-stop-index-v1", "status": "RUNNING",
             "cache": receipt, "candidate_id": None, "target_online_ms": None, "cases": []}
    save(HERE / "index.json", index)
    for cohort, frozen in cases:
        p, q = frozen["p"], frozen["q"]
        journal_path = case_dir / f"p{p}.jsonl"
        summary_path = case_dir / f"p{p}-summary.json"
        model = H.Reduced(p, functions, jfun13, [2, 5, 13])
        assert int(model.E.cardinality()) == frozen["class"]["curve_order"]
        sage_points = [model.E(x, y) for x, y in frozen["class"]["class_points"]]
        points = [tuple(x) for x in frozen["class"]["class_points"]]
        neg, add = R.group_law(p)
        baseline = [I.sparse(x["row"]) for x in frozen["class"]["base_rows"] + frozen["direct_candidates"]]
        basis = I.RankBasis(q, baseline)
        assert basis.rank == frozen["baseline_rank_mod_q"]
        four = I.PairIndex(points, neg, add)
        five = Five.FiveIndex(points, neg, add, PLAN["support_five_row_cap"],
                              PLAN["support_five_wall_cap_seconds"])
        wide = WideIndex(points, neg, add, PLAN["wide_row_cap"], PLAN["wide_wall_cap_seconds"])
        basis_eight = I.RankBasis(q, baseline)
        eight = RankStopEightIndex(points, neg, add, PLAN["support_eight_row_cap"],
                                   PLAN["support_eight_wall_cap_seconds"], PLAN["support_eight_probe_cap"],
                                   basis_eight, PLAN["rank_goal"])
        cache = {}
        summary = {"cohort": cohort, "p": p, "q": q, "baseline_rank_mod_q": basis.rank,
                   "status": "RUNNING", "rank_goal_status": "UNKNOWN",
                   "candidate_id": None, "target_online_ms": None}
        phase_times = []
        all_rows = list(baseline)
        all_rows_eight = list(baseline)
        first_seven = first_eight = None
        first_eight_rows = None
        with journal_path.open("x", encoding="utf-8") as journal:
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
                row_groups = {"four": [], "five": [], "six": [], "seven": [], "eight": []}
                four_metrics = five_metrics = wide_metrics = eight_metrics = {}
                four_ns = five_ns = wide_ns = eight_ns = rank_ns = 0
                novel = {name: 0 for name in row_groups}
                novel_eight = 0
                step_status = entry["status"]
                if step_status == "OUTSIDE_CLASS_TRACE":
                    t0 = time.perf_counter_ns()
                    row_groups["four"], four_metrics = four.append(entry)
                    four_ns = time.perf_counter_ns() - t0
                    t0 = time.perf_counter_ns()
                    row_groups["five"], five_metrics = five.append(entry)
                    five_ns = time.perf_counter_ns() - t0
                    if five_metrics["status"] == "COMPLETE":
                        t0 = time.perf_counter_ns()
                        row_groups["six"], row_groups["seven"], wide_metrics = wide.append(entry)
                        wide_ns = time.perf_counter_ns() - t0
                        step_status = wide_metrics["status"]
                    else:
                        step_status = five_metrics["status"]
                    t0 = time.perf_counter_ns()
                    for name in ("four", "five", "six", "seven"):
                        for row in row_groups[name]:
                            sparse = I.sparse(row["row"])
                            novel[name] += bool(basis.insert(sparse))
                            all_rows.append(sparse)
                            basis_eight.insert(sparse)
                            all_rows_eight.append(sparse)
                    rank_ns = time.perf_counter_ns() - t0
                    if basis.rank >= PLAN["rank_goal"] and first_seven is None:
                        first_seven = k + 1
                    if step_status == "COMPLETE":
                        if first_eight is not None:
                            eight_metrics = {"status": "SKIPPED_RANK_GOAL", "step_probes": 0,
                                             "matches": 0, "triple_insertions": 0,
                                             "rank_novel": 0, "rank_check_wall_ns": 0,
                                             "eight_wall_ns": 0}
                        elif basis_eight.rank >= PLAN["rank_goal"]:
                            first_eight = k + 1
                            first_eight_rows = list(all_rows_eight)
                            eight_metrics = {"status": "SKIPPED_LOWER_RANK_GOAL", "step_probes": 0,
                                             "matches": 0, "triple_insertions": 0,
                                             "rank_novel": 0, "rank_check_wall_ns": 0,
                                             "eight_wall_ns": 0}
                        else:
                            t0 = time.perf_counter_ns()
                            row_groups["eight"], eight_metrics = eight.append(entry)
                            eight_ns = time.perf_counter_ns() - t0
                            novel_eight = eight_metrics["rank_novel"]
                            all_rows_eight.extend(I.sparse(row["row"]) for row in row_groups["eight"])
                            if eight_metrics["status"] == "RANK_GOAL_REACHED":
                                first_eight = k + 1
                                first_eight_rows = list(all_rows_eight)
                            elif eight_metrics["status"] != "COMPLETE":
                                step_status = eight_metrics["status"]
                record = {"source": k, "entry": entry, "step_status": step_status,
                          "rows": row_groups, "novel": novel,
                          "four_metrics": four_metrics, "five_metrics": five_metrics,
                          "wide_metrics": wide_metrics, "eight_metrics": eight_metrics,
                          "rank_mod_q": basis.rank, "rank_eight_mod_q": basis_eight.rank,
                          "novel_eight": novel_eight,
                          "lift_wall_ns": lift_ns, "four_wall_ns": four_ns,
                          "five_wall_ns": five_ns, "wide_wall_ns": wide_ns,
                          "eight_wall_ns": eight_ns,
                          "rank_wall_ns": rank_ns}
                t0 = time.perf_counter_ns()
                journal.write(json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n")
                journal.flush()
                os.fsync(journal.fileno())
                phase_times.append({"source": k, "checkpoint_wall_ns": time.perf_counter_ns() - t0})
                if step_status != "COMPLETE":
                    summary["status"] = "CENSORED_SOURCE_OR_SEARCH"
                    break
                if basis.rank >= PLAN["rank_goal"]:
                    summary.update({"status": "RANK_GOAL_REACHED", "rank_goal_status": "ACHIEVED"})
                    break
            else:
                summary.update({"status": "FULL_POOL_BELOW_RANK_GOAL",
                                "rank_goal_status": "BOUNDED_BELOW_GOAL"})
            summary["collector_wall_ns"] = time.perf_counter_ns() - collector_start
        recorded = records(journal_path)
        summary["source_count"] = len(recorded)
        summary["final_rank_mod_q"] = basis.rank
        summary["row_counts"] = {"four": len(four.rows), "five": len(five.rows),
                                 "six": len(wide.six_rows), "seven": len(wide.seven_rows),
                                 "eight": len(eight.rows)}
        summary["novel_directions"] = {name: sum(x["novel"][name] for x in recorded)
                                         for name in ("four", "five", "six", "seven")}
        summary["novel_directions"]["eight"] = sum(x["novel_eight"] for x in recorded)
        summary["final_rank_eight_mod_q"] = basis_eight.rank
        summary["first_seven_source_count"] = first_seven
        summary["first_eight_source_count"] = first_eight
        summary["actual_eight_probes"] = eight.probes
        summary["whole_prefix_eight_probes"] = 32 * comb(first_eight, 5) if first_eight is not None else None
        summary["paired_horizon_eight_probes"] = 32 * comb(len(recorded), 5)
        summary["saved_eight_probes"] = summary["paired_horizon_eight_probes"] - eight.probes if first_eight is not None else 0
        summary["saved_within_prefix_probes"] = summary["whole_prefix_eight_probes"] - eight.probes if first_eight is not None else 0
        summary["saved_after_prefix_probes"] = summary["paired_horizon_eight_probes"] - summary["whole_prefix_eight_probes"] if first_eight is not None else 0
        assert summary["saved_eight_probes"] >= 0
        assert summary["saved_within_prefix_probes"] >= 0
        assert summary["saved_eight_probes"] == summary["saved_within_prefix_probes"] + summary["saved_after_prefix_probes"]
        for name, field in (("lift_sum_ns", "lift_wall_ns"), ("four_sum_ns", "four_wall_ns"),
                            ("five_sum_ns", "five_wall_ns"), ("wide_sum_ns", "wide_wall_ns"),
                            ("rank_sum_ns", "rank_wall_ns"), ("eight_sum_ns", "eight_wall_ns")):
            summary[name] = sum(x[field] for x in recorded)
        summary["six_sum_ns"] = sum(x["wide_metrics"].get("six_wall_ns", 0) for x in recorded)
        summary["seven_sum_ns"] = sum(x["wide_metrics"].get("seven_wall_ns", 0) for x in recorded)
        summary["triple_update_sum_ns"] = sum(x["wide_metrics"].get("triple_update_wall_ns", 0) for x in recorded)
        summary["wide_setup_sum_ns"] = summary["wide_sum_ns"] - sum(summary[name] for name in
            ("six_sum_ns", "seven_sum_ns", "triple_update_sum_ns"))
        assert summary["wide_setup_sum_ns"] >= 0
        summary["checkpoint_phase_times"] = phase_times
        summary["checkpoint_sum_ns"] = sum(x["checkpoint_wall_ns"] for x in phase_times)
        summary["loop_overhead_ns"] = summary["collector_wall_ns"] - sum(summary[name] for name in
            ("lift_sum_ns", "four_sum_ns", "five_sum_ns", "wide_sum_ns", "eight_sum_ns", "rank_sum_ns", "checkpoint_sum_ns"))
        assert summary["loop_overhead_ns"] >= 0
        if summary["rank_goal_status"] == "ACHIEVED":
            t0 = time.perf_counter_ns()
            summary.update(anchored_logs(q, frozen["class"]["curve_order"], sage_points, all_rows))
            summary["anchor_replay_wall_ns"] = time.perf_counter_ns() - t0
        if first_eight_rows is not None:
            t0 = time.perf_counter_ns()
            summary["eight_replay"] = anchored_logs(q, frozen["class"]["curve_order"], sage_points, first_eight_rows)
            summary["eight_anchor_replay_wall_ns"] = time.perf_counter_ns() - t0
        save(summary_path, summary)
        index["cases"].append({"cohort": cohort, "p": p, "q": q,
                               "journal": journal_path.relative_to(HERE).as_posix(),
                               "journal_sha256": sha(journal_path),
                               "summary": summary_path.relative_to(HERE).as_posix(),
                               "summary_sha256": sha(summary_path),
                               "status": summary["status"], "source_count": summary["source_count"],
                               "final_rank_mod_q": basis.rank,
                               "final_rank_eight_mod_q": basis_eight.rank,
                               "first_seven_source_count": first_seven,
                               "first_eight_source_count": first_eight,
                               "actual_eight_probes": eight.probes,
                               "saved_within_prefix_probes": summary["saved_within_prefix_probes"],
                               "saved_eight_probes": summary["saved_eight_probes"]})
        save(HERE / "index.json", index)
        print(json.dumps(index["cases"][-1]), flush=True)
    index["status"] = "COMPLETE" if all(x["status"] in
        ("RANK_GOAL_REACHED", "FULL_POOL_BELOW_RANK_GOAL") for x in index["cases"]) else "CENSORED"
    save(HERE / "index.json", index)


if __name__ == "__main__":
    main()
