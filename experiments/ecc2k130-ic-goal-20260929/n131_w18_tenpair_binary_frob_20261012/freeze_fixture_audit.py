"""Bind the independent Sage replay before checking the constructed control."""

import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
NINE = ROOT / "n131_fixed_seed_ninepair_cubic_20261011"
assert not (HERE / "fixture_audit_protocol.json").exists()
paths = {
    "source": HERE / "audit_fixture_sage.py",
    "fixture": HERE / "control_fixture.json",
    "prior_fixture": NINE / "control_fixture.json",
    "prior_sage_audit": NINE / "sage_fixture_result.json",
    "support": ROOT / "n131_w16_w18_sixpair_width_gate_20261010/support_w18.tsv",
    "runtime": HERE / "sage_runtime_info.json",
}
assert json.loads(paths["runtime"].read_text())["status"] == "verified"
protocol = {"status": "FROZEN_N131_TENPAIR_CONSTRUCTED_SAGE_REPLAY",
            "candidate_id": None,
            "sha256": {name: hashlib.sha256(path.read_bytes()).hexdigest()
                       for name, path in paths.items()}}
(HERE / "fixture_audit_protocol.json").write_text(json.dumps(protocol, sort_keys=True, indent=2) + "\n")
print(protocol["status"])
