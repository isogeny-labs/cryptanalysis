"""Freeze exact formula, runner, solver, and capped comparison."""

import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
build = json.loads((HERE / "build_result.json").read_text())
assert build["status"] == "FORMULAS_BUILT"
solver = Path("/opt/homebrew/bin/cryptominisat5")
sources = [HERE / name for name in
           ("build.py", "build_result.json", "constructed_positive.xcnf",
            "public_same_regions.xcnf", "run.py")]
sources += [solver,
            HERE.parent / "n41_product_region_span_gate_20261013" / "terminal.json",
            HERE.parent / "n41_bilinear_rank_screen_20261013" / "sage_result.json"]
for case in build["cases"]:
    name = case["name"]
    assert hashlib.sha256((HERE / f"{name}.xcnf").read_bytes()).hexdigest() == case["formula_sha256"]
protocol = {"status": "FROZEN", "kind": "n41_symbolic_four_family_label_sat",
            "curve_id": "EC1N41Ckb1h023d9a38bbf7",
            "solver": str(solver), "worker_count": 1,
            "solver_cap_seconds": 30, "parent_cap_seconds": 35,
            "rss_cap_bytes": 4294967296, "cases": build["cases"],
            "sources": {str(path): hashlib.sha256(path.read_bytes()).hexdigest()
                        for path in sources}}
with (HERE / "protocol.json").open("x") as stream:
    json.dump(protocol, stream, indent=2, sort_keys=True)
    stream.write("\n")
