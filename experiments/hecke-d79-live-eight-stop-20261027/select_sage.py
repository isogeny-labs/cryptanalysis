"""Freeze a disjoint D79 panel for the live support-eight early-stop collector."""
import hashlib
import importlib.util
import json
from pathlib import Path

from sage.all import EllipticCurve, GF, factor, hilbert_class_polynomial, is_prime

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
PLAN = json.loads((HERE / "inputs.json").read_text())


def pinned(item):
    path = ROOT / item["path"]
    assert hashlib.sha256(path.read_bytes()).hexdigest() == item["sha256"]
    return path


def module(item, name):
    path = pinned(item)
    spec = importlib.util.spec_from_file_location(name, path)
    out = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(out)
    return out


def save(out):
    (HERE / "selection.json").write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")


def main():
    C = module(PLAN["frozen"]["class_builder"], "transfer_class_builder")
    R = module(PLAN["frozen"]["relation_helpers"], "transfer_relation_helpers")
    H = module(PLAN["frozen"]["hecke_source"], "transfer_hecke_source")
    funcs, jfun = H.build([2, 5])
    H79 = hilbert_class_polynomial(-79)
    checked, selected = [], []
    for v in range(PLAN["v_start"], PLAN["v_end"] + 1, 2):
        p = v*v + 316
        if not is_prime(p):
            continue
        E = EllipticCurve(GF(p), [0, -1, 1, -10, -20])
        n = int(E.cardinality())
        q = int(max(prime for prime, _ in factor(n)))
        if not (n % 5 == 0 and (p - 1) % 5 != 0 and q >= 53):
            continue
        try:
            cell = C.class_case(H, funcs, jfun, H79, p, v, n, q)
        except Exception as exc:
            cell = {"p": p, "v": v, "status": "CLASS_CONSTRUCTION_ERROR", "error_type": type(exc).__name__}
        checked.append(cell)
        if cell["status"] == "CLASS_READY":
            points = [tuple(x) for x in cell["class_points"]]
            neg, add = R.group_law(p)
            direct, trials = R.direct_rows(points, neg, add)
            baseline = [R.sparse(x["row"]) for x in cell["base_rows"] + direct]
            rank = R.rank(baseline, q)
            selected.append({"p": p, "q": q, "class": cell, "direct_candidates": direct,
                             "direct_trial_count": trials, "baseline_rank_mod_q": rank})
        out = {"schema": "hecke-d79-live-eight-stop-selection-v1", "status": "RUNNING",
               "checked_eligible_cases": checked, "selected": selected,
               "candidate_id": None, "target_online_ms": None}
        save(out)
        print(json.dumps({"p": p, "class_status": cell["status"],
                          "baseline_rank": selected[-1]["baseline_rank_mod_q"] if cell["status"] == "CLASS_READY" else None}), flush=True)
        if len(selected) == PLAN["target_ready_classes"] or len(checked) == PLAN["max_eligible_classes"]:
            break
    out["status"] = "CLASSES_FROZEN" if len(selected) == PLAN["target_ready_classes"] else "SELECTION_SHORTAGE"
    save(out)
    print(json.dumps({"status": out["status"], "selected_p": [x["p"] for x in selected]}))


if __name__ == "__main__":
    main()
