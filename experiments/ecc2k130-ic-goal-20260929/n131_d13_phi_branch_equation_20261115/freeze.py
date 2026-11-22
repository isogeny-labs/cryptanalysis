"""Freeze exact N131 chart audit and its claim boundary."""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
GOAL = HERE.parent
ROOT = HERE.parents[2]
GEOMETRY = GOAL / "n131_phi_torsion_frobenius_domains_20261005" / "m12_d13_static" / "d13_exact_geometry_v1.json"
RAW = GOAL / "n131_d13_phi_raw_fiber_20261115" / "audit_result.json"
EXPANDED = GOAL / "n131_d13_phi_expanded_base_20261115" / "census_result.json"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    geometry = json.loads(GEOMETRY.read_text())
    raw = json.loads(RAW.read_text())
    assert raw["status"] == "PASS_ALL_VALID_SELECTORS"
    assert geometry["curve_id"] == json.loads(EXPANDED.read_text())["curve_id"]
    inputs = {"geometry": GEOMETRY, "raw_audit": RAW,
              "expanded_census": EXPANDED,
              "field_source": ROOT / "ecc2k130" / "codegen" / "field.py",
              "curve_source": ROOT / "ecc2k130" / "codegen" / "curves.py",
              "audit_curve_source": ROOT / "ecc2k130" / "codegen" / "indexcalc_e2e.py"}
    record = {
        "kind": "n131_d13_adjacent_union_phi_branch_protocol_v1",
        "status": "FROZEN_BEFORE_AUDIT",
        "frozen_utc": datetime.now(timezone.utc).isoformat(),
        "candidate_id": None,
        "proposal_id": "Q20261115082001",
        "curve_id": geometry["curve_id"],
        "workload_id": geometry["workload_id"],
        "inputs": {k: str(v) for k, v in inputs.items()},
        "input_sha256": {k: sha(v) for k, v in inputs.items()},
        "audit_source_sha256": sha(HERE / "audit.py"),
        "lean_source_sha256": sha(HERE / "BranchEquation.lean"),
        "wall_cap_seconds": 180,
        "rss_cap_bytes": 4*1024**3,
        "hypothesis": "For every valid d13 raw selector, the original and adjacent image phi charts satisfy the single Boolean branch equation and the image denominator is nonzero.",
        "claim_boundary": "Exact source algebra and finite census only. The sparse-multiplier count is a construction bound, not a measured SAT formula or query cost.",
    }
    path = HERE / "protocol.json"
    assert not path.exists()
    path.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    print(path)


if __name__ == "__main__":
    main()
