"""Lift four fresh classes and replay direct-degree source orders."""
import hashlib
import importlib.util
import json
import math
import sys
import time
from pathlib import Path

from sage.all import classical_modular_polynomial

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
PLAN = json.loads((HERE / "inputs.json").read_text())
POST = json.loads((HERE / "post-selection.json").read_text())


def pinned(item):
    path = ROOT / item["path"]
    assert hashlib.sha256(path.read_bytes()).hexdigest() == item["sha256"]
    return path


def module(item, name):
    spec = importlib.util.spec_from_file_location(name, pinned(item))
    out = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(out)
    return out


def save(out):
    (HERE / "challenge.json").write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")


def main():
    raw = (HERE / "selection.json").read_bytes()
    assert hashlib.sha256(raw).hexdigest() == POST["selection_sha256"]
    selection = json.loads(raw)
    assert selection["status"] == "ORDERS_FROZEN" and len(selection["selected"]) == PLAN["target_ready_classes"]
    f = PLAN["frozen"]
    H = module(f["hecke_source"], "transfer_lift_hecke")
    P = module(f["prefix_runner"], "transfer_lift_prefix")
    R = module(f["relation_helpers"], "transfer_lift_relations")
    S = module(f["shared_build"], "transfer_lift_build")
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
    modpoly = classical_modular_polynomial(13)
    out = {"schema": "hecke-d79-direct-degree-order-panel-challenge-v1", "status": "RUNNING",
           "cache": cache_receipt, "cases": [], "candidate_id": None, "target_online_ms": None}
    save(out)
    for frozen in selection["selected"]:
        p, q = frozen["p"], frozen["q"]
        cell = {"p": p, "q": q, "status": "RUNNING", "source_entries": [],
                "baseline_rank_mod_q": frozen["baseline_rank_mod_q"],
                "candidate_id": None, "target_online_ms": None}
        out["cases"].append(cell)
        save(out)
        try:
            model = H.Reduced(p, {**funcs25, **funcs13}, jfun13, [2, 5, 13])
            assert int(model.E.cardinality()) == frozen["class"]["curve_order"]
            sage_points = [model.E(x, y) for x, y in frozen["class"]["class_points"]]
            points = [tuple(x) for x in frozen["class"]["class_points"]]
            neg, add = R.group_law(p)
            baseline = [R.sparse(x["row"]) for x in frozen["class"]["base_rows"] + frozen["direct_candidates"]]
            assert R.rank(baseline, q) == cell["baseline_rank_mod_q"]
            cache = {}
            entries = {}
            for i, point in enumerate(sage_points):
                t0 = time.perf_counter_ns()
                poly = model.neighbour_x(13, point)
                pattern = [[int(f.degree()), int(mult)] for f, mult in poly.factor()]
                degree = math.lcm(*(d for d, _ in pattern))
                if degree > 12 or any(mult != 1 for _, mult in pattern):
                    entry = {"source": i, "factor_pattern": pattern, "splitting_degree": degree,
                             "status": "CENSORED_EXTENSION_OR_MULTIPLICITY"}
                else:
                    entry, _ = P.lift_source(i, point, model, jfun13, sage_points, {}, cache, modpoly, pattern)
                entry["lift_wall_ns"] = time.perf_counter_ns() - t0
                cell["source_entries"].append(entry)
                if entry["status"] == "OUTSIDE_CLASS_TRACE":
                    entries[i] = entry
                save(out)
            cell["source_lift_sum_ns"] = sum(x["lift_wall_ns"] for x in cell["source_entries"])
            if len(entries) != 40:
                cell.update({"status": "CENSORED_SOURCE", "full_pool_rank_mod_q": None,
                             "order_results": None})
            else:
                relations, trials = R.hecke_rows(entries, points, neg, add)
                rows = [(set(x["sources"]), R.sparse(x["row"])) for x in relations]
                full_rank = R.rank(baseline + [row for _, row in rows], q)
                order_results = {}
                for name, order in frozen["source_orders"].items():
                    prefixes = []
                    seen = set()
                    for count in range(41):
                        if count:
                            seen.add(order[count - 1])
                        subset = [row for support, row in rows if support <= seen]
                        prefixes.append({"source_count": count, "rank_mod_q": R.rank(baseline + subset, q),
                                         "hecke_rows": len(subset),
                                         "lift_sum_ns": sum(entries[i]["lift_wall_ns"] for i in seen)})
                    assert prefixes[-1]["rank_mod_q"] == full_rank
                    first = next((x["source_count"] for x in prefixes if x["rank_mod_q"] >= PLAN["rank_goal"]), None)
                    order_results[name] = {"first_rank_goal_source_count": first, "prefixes": prefixes}
                cell.update({"status": "COMPLETE", "hecke_candidate_count": len(relations),
                             "hecke_trial_count": trials, "full_pool_rank_mod_q": full_rank,
                             "order_results": order_results})
        except Exception as exc:
            cell.update({"status": "SOURCE_OR_ANALYSIS_EXCEPTION", "error_type": type(exc).__name__,
                         "full_pool_rank_mod_q": None, "order_results": None})
        save(out)
        print(json.dumps({"p": p, "status": cell["status"], "full_rank": cell["full_pool_rank_mod_q"],
                          "first_counts": None if cell["order_results"] is None else
                          {k: v["first_rank_goal_source_count"] for k, v in cell["order_results"].items()}}), flush=True)
    out["status"] = "COMPLETE"
    save(out)


if __name__ == "__main__":
    main()
