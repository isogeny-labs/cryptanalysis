"""Freeze selected bit order and 100 untouched rectangle identities."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
prior = json.loads((HERE / "protocol_v2.json").read_text())
selection = json.loads((HERE / "selection_result.json").read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


assert selection["status"] == "PASS_N41_DISJOINT_CUBIC_BIT_SELECTION"
assert selection["training_rectangles"] == 32
assert selection["holdout_rectangles"] == 100
sources = dict(prior["sources"])
for name, path in {
    "selection_protocol": HERE / "selection_protocol.json",
    "selection_result": HERE / "selection_result.json",
    "producer_adaptive": HERE / "run_adaptive.py",
    "auditor_adaptive": HERE / "audit_adaptive.py",
    "freeze_adaptive": HERE / "freeze_adaptive.py",
}.items():
    sources[name] = {"path": str(path), "sha256": sha(path)}
record = {key: value for key, value in prior.items()
          if key not in ("sources", "rectangles", "selection", "status")}
record.update({"status": "FROZEN_N41_ADAPTIVE_SYMBOLIC_HOLDOUT",
               "selection": "The last 100 of 132 sorted complete 2x2 rectangles are a disjoint holdout. The 15-bit order was fixed from the first 32 before holdout root outcomes were read.",
               "bit_order": selection["bit_order"],
               "rectangles": prior["rectangles"][32:],
               "sources": sources})
assert len(record["rectangles"]) == 100
assert any(966 in row["case_indices"] for row in record["rectangles"])
assert not (HERE / "adaptive_protocol.json").exists()
(HERE / "adaptive_protocol.json").write_text(json.dumps(record, sort_keys=True, indent=2) + "\n")
