"""Frozen negative first-product panel for the specialized one-sided XCNF."""
import hashlib
import importlib.util
import json
import statistics
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("specialized", HERE / "run_specialized.py")
specialized = importlib.util.module_from_spec(spec)
spec.loader.exec_module(specialized)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    protocol = json.loads((HERE / "panel_protocol.json").read_text())
    for name, path in (("runner", HERE / "run_panel.py"),
                       ("specialized_runner", HERE / "run_specialized.py"),
                       ("joint_runner", specialized.PRIOR / "run.py"),
                       ("solver", specialized.SOLVER)):
        assert sha(path) == protocol["sha256"][name]
    started = time.monotonic_ns()
    source = specialized.joint.source("n131_positive")
    setup = time.monotonic_ns() - started
    rows = []
    for index, mask in enumerate(protocol["first_product_masks"]):
        label = "panel_%02d" % index
        specialized.run_one(label, mask, protocol, source)
        rows.append(json.loads((HERE / (label + ".small.json")).read_text()))
    solver_ms = [r["phase_ns_exploratory"]["solver"] / 1e6 for r in rows]
    total_ms = [sum(r["phase_ns_exploratory"][k] for k in
                    ("anf_specialize", "formula_emit", "solver", "model_check")) / 1e6
                for r in rows]
    result = {"status": "COMPLETE_FROZEN_PANEL", "source_build_ns_exploratory": setup,
              "cases": len(rows), "first_product_masks": protocol["first_product_masks"],
              "statuses": {s: sum(r["status"] == s for r in rows)
                           for s in sorted(set(r["status"] for r in rows))},
              "solver_ms_exploratory": {"min": min(solver_ms),
                                         "median": statistics.median(solver_ms),
                                         "max": max(solver_ms)},
              "per_product_full_ms_exploratory": {"min": min(total_ms),
                                                    "median": statistics.median(total_ms),
                                                    "max": max(total_ms)},
              "anf_monomials": [r["specialized_anf_monomials"] for r in rows],
              "formula_bytes": [r["formula"]["bytes"] for r in rows]}
    (HERE / "panel_result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print("PANEL", result["statuses"], result["solver_ms_exploratory"],
          result["per_product_full_ms_exploratory"], flush=True)


if __name__ == "__main__":
    main()
