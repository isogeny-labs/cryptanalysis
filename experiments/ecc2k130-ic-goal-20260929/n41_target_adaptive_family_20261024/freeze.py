"""Freeze the same two N41 boxes for an exact Fermat zero-test comparison."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
PRIOR = ROOT / "n41_four_code_suffix_quotient_20261024"
prior = json.loads((PRIOR / "protocol.json").read_text())
assert prior["status"] == "FROZEN_N41_FOUR_CODE_SUFFIX_QUOTIENT"
assert [row["label"] for row in prior["boxes"]] == ["control", "witness"]
SOURCES = {name: Path(source["path"]) for name, source in prior["sources"].items()
           if name not in ("sage_runtime", "producer", "auditor", "freeze")}
SOURCES.update({"prior_protocol": PRIOR / "protocol.json",
                "prior_result": PRIOR / "result.json",
                "sage_runtime": HERE / "sage_runtime_info.json",
                "producer": HERE / "run.py",
                "auditor": HERE / "audit_sage.py",
                "freeze": HERE / "freeze.py"})


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


record = {"status": "FROZEN_N41_FOUR_CODE_FERMAT_ZERO",
          "candidate_id": None, "curve_id": prior["curve_id"],
          "field_degree": 41, "field_modulus": [41, 3, 0],
          "suffix_state_ids": prior["suffix_state_ids"],
          "eligible_quads": prior["eligible_quads"],
          "complete_boxes": prior["complete_boxes"],
          "boxes": prior["boxes"],
          "exponent": 2**41-1,
          "addition_chain_lengths": [1, 2, 4, 5, 10, 20, 40, 41],
          "selection": "Exact two boxes copied from the previously frozen trace-bit run before this producer executes.",
          "worker_count": 1, "wall_cap_seconds": 300,
          "rss_cap_bytes": 4*1024**3,
          "sources": {name: {"path": str(path), "sha256": sha(path)}
                      for name, path in SOURCES.items()}}
assert not (HERE / "protocol.json").exists()
(HERE / "protocol.json").write_text(json.dumps(record, sort_keys=True, indent=2) + "\n")
