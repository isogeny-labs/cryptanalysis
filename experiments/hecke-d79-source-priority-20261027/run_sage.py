"""Lift each frozen source once, then replay two precommitted source orders."""
import hashlib
import importlib.util
import json
import math
import sys
import time
from pathlib import Path

from sage.all import GF, classical_modular_polynomial, matrix, vector

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
PLAN = json.loads((HERE / "inputs.json").read_text())
SEAL = json.loads((HERE / "post-selection.json").read_text())


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


def anchor_logs(q, n, sage_points, rows):
    F = GF(q)
    projected = [(n // q) * point for point in sage_points]
    zero = sage_points[0].curve()(0)
    anchor = next(i for i, point in enumerate(projected) if point != zero)
    T = projected[anchor]
    assert int(T.order()) == q
    A = matrix(F, len(rows), 40, lambda i, j: rows[i].get(j, 0))
    assert int(A.rank()) == 39
    anchored = A.stack(matrix(F, 1, 40, lambda _, j: int(j == anchor)))
    assert int(anchored.rank()) == 40
    logs = [int(x) for x in anchored.solve_right(vector(F, [0] * len(rows) + [1]))]
    assert all(log * T == point for log, point in zip(logs, projected))
    return {"anchor_index": anchor, "anchored_logs": logs, "replay": "PASS"}


def replay(case, entries, order, points, sage_points, I, R):
    q = case["q"]
    baseline = [I.sparse(row["row"]) for row in case["class"]["base_rows"] + case["direct_candidates"]]
    basis = I.RankBasis(q, baseline)
    assert basis.rank == case["baseline_rank_mod_q"]
    neg, add = R.group_law(case["p"])
    index = I.PairIndex(points, neg, add)
    out = {"status": "RUNNING", "baseline_rank": basis.rank, "steps": [], "candidate_id": None,
           "target_online_ms": None}
    all_rows = list(baseline)
    start = time.perf_counter_ns()
    for k, source in enumerate(order):
        entry = dict(entries[source])
        if entry["status"] != "OUTSIDE_CLASS_TRACE":
            out["status"] = "CENSORED_SOURCE"
            out["steps"].append({"prefix": k + 1, "original_source": source, "status": entry["status"]})
            break
        entry["source"] = k
        new_rows, metrics = index.append(entry)
        novel = 0
        for item in new_rows:
            sparse = I.sparse(item["row"])
            novel += bool(basis.insert(sparse))
            all_rows.append(sparse)
        out["steps"].append({"prefix": k + 1, "original_source": source,
                             "new_rows": len(new_rows), "novel_rows": novel,
                             "rank_mod_q": basis.rank, **metrics})
        if basis.rank >= PLAN["rank_goal"]:
            out["status"] = "RANK_GOAL_REACHED"
            break
    else:
        out["status"] = "FULL_POOL_BELOW_RANK_GOAL"
    out["replay_wall_ns"] = time.perf_counter_ns() - start
    out["stop_prefix"] = len(out["steps"])
    out["final_rank_mod_q"] = basis.rank
    out["verified_rows"] = len(index.rows)
    out["novel_rows"] = basis.rank - case["baseline_rank_mod_q"]
    if out["status"] == "RANK_GOAL_REACHED":
        out["anchor"] = anchor_logs(q, case["class"]["curve_order"], sage_points, all_rows)
    return out


def main():
    assert sha(HERE / "selection.json") == SEAL["selection_sha256"]
    assert sha(HERE / "inputs.json") == SEAL["inputs_sha256"]
    assert sha(HERE / "select_sage.py") == SEAL["selector_sha256"]
    selected = json.loads((HERE / "selection.json").read_text())
    assert selected["status"] == "CLASSES_FROZEN"
    assert [x["p"] for x in selected["selected"]] == SEAL["selected_p"]
    I = module(PLAN["incremental_module"], "priority_incremental")
    f = PLAN["frozen"]
    H = module(f["hecke_source"], "priority_hecke")
    P = module(f["prefix_runner"], "priority_prefix")
    R = module(f["relation_helpers"], "priority_relations")
    S = module(f["shared_build"], "priority_build")
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
    case_dir.mkdir(exist_ok=True)
    result = {"schema": "hecke-d79-source-priority-v1", "status": "RUNNING",
              "selection_sha256": SEAL["selection_sha256"], "cache": receipt,
              "candidate_id": None, "target_online_ms": None, "cases": []}
    save(HERE / "result.json", result)
    for case in selected["selected"]:
        p = case["p"]
        model = H.Reduced(p, functions, jfun13, [2, 5, 13])
        assert int(model.E.cardinality()) == case["class"]["curve_order"]
        sage_points = [model.E(x, y) for x, y in case["class"]["class_points"]]
        points = [tuple(x) for x in case["class"]["class_points"]]
        cache = {}
        entries = []
        start = time.perf_counter_ns()
        for i, point in enumerate(sage_points):
            poly = model.neighbour_x(13, point)
            pattern = [[int(factor.degree()), int(mult)] for factor, mult in poly.factor()]
            degree = math.lcm(*(d for d, _ in pattern))
            if degree > 12 or any(mult != 1 for _, mult in pattern):
                entry = {"source": i, "factor_pattern": pattern, "splitting_degree": degree,
                         "status": "CENSORED_EXTENSION_OR_MULTIPLICITY"}
            else:
                entry, _ = P.lift_source(i, point, model, jfun13, sage_points, {}, cache, modpoly, pattern)
            entries.append(entry)
        lift_wall_ns = time.perf_counter_ns() - start
        assert len(entries) == 40
        orders = case["source_orders"]
        assert sorted(orders["original"]) == sorted(orders["low_incidence"]) == list(range(40))
        comparisons = {name: replay(case, entries, order, points, sage_points, I, R)
                       for name, order in orders.items()}
        artifact = {"p": p, "q": case["q"], "baseline_rank": case["baseline_rank_mod_q"],
                    "source_orders": orders, "entries": entries, "lift_wall_ns": lift_wall_ns,
                    "comparisons": comparisons, "candidate_id": None, "target_online_ms": None}
        path = case_dir / f"p{p}.json"
        save(path, artifact)
        result["cases"].append({"p": p, "q": case["q"], "path": path.relative_to(HERE).as_posix(),
                                "sha256": sha(path), "orders": {name: {"status": x["status"],
                                "stop_prefix": x["stop_prefix"], "final_rank_mod_q": x["final_rank_mod_q"]}
                                for name, x in comparisons.items()}})
        save(HERE / "result.json", result)
        print(json.dumps({"p": p, "orders": result["cases"][-1]["orders"]}), flush=True)
    result["status"] = "COMPLETE"
    save(HERE / "result.json", result)


if __name__ == "__main__":
    main()
