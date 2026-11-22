"""Freeze each bounded census phase before launching it."""

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
GEOMETRY = HERE.parent / "n131_phi_torsion_frobenius_domains_20261005" / "m12_d13_static" / "d13_exact_geometry_v1.json"
EXPANDED = HERE.parent / "n131_d13_phi_expanded_base_20261115" / "census_result.json"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def freeze_census():
    geometry = json.loads(GEOMETRY.read_text())
    record = {
        "kind": "n131_d13_union_raw_cofactor_census_protocol_v1",
        "status": "FROZEN_BEFORE_CENSUS",
        "frozen_utc": datetime.now(timezone.utc).isoformat(),
        "proposal_id": "Q20261115082001",
        "candidate_id": None,
        "curve_id": geometry["curve_id"],
        "workload_id": geometry["workload_id"],
        "subgroup_order": "680564733841876926932320129493409985129",
        "inputs": {"geometry": str(GEOMETRY), "expanded_census": str(EXPANDED)},
        "input_sha256": {"geometry": sha(GEOMETRY), "expanded_census": sha(EXPANDED)},
        "source_sha256": sha(HERE / "census.py"),
        "sage_runtime_info_sha256": sha(HERE / "sage_runtime_info.json"),
        "wall_cap_seconds": 240,
        "rss_cap_bytes": 4 * 1024**3,
        "hypothesis": "For every exact d13 selector, the raw 1+tau image lies in an even rational four-torsion cofactor class; quantify source and image class counts and verify the projected map.",
        "decision_gate": "Use exact raw class counts to form a class-conditioned convolution; do not promote a uniform four-fiber model or N131 solver-cost claim from this census alone.",
    }
    path = HERE / "protocol.json"
    assert not path.exists()
    path.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    print(path)


def freeze_audit():
    census = HERE / "census_result.json"
    assert census.exists()
    protocol = json.loads((HERE / "protocol_v2.json").read_text())
    record = {
        "kind": "n131_d13_union_raw_cofactor_sage_audit_protocol_v1",
        "status": "FROZEN_BEFORE_AUDIT",
        "frozen_utc": datetime.now(timezone.utc).isoformat(),
        "subgroup_order": protocol["subgroup_order"],
        "inputs": {"geometry": str(GEOMETRY), "census_result": str(census)},
        "input_sha256": {"geometry": sha(GEOMETRY), "census_result": sha(census)},
        "source_sha256": sha(HERE / "audit_sage.py"),
        "sage_runtime_info_sha256": sha(HERE / "sage_runtime_info.json"),
        "wall_cap_seconds": 240,
        "rss_cap_bytes": 4 * 1024**3,
        "comparison": "Reconstruct every valid source x in an independent polynomial-field Sage model and match ordered sign-class pairs and raw image x digest.",
    }
    path = HERE / "audit_protocol.json"
    assert not path.exists()
    path.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    print(path)


def freeze_amendment():
    old = HERE / "protocol.json"
    record = json.loads(old.read_text())
    assert record["source_sha256"] == sha(HERE / "census_v1.py")
    assert (HERE / "census.stderr.txt").read_text().endswith("AssertionError\n")
    failure = {
        "kind": "n131_d13_union_raw_census_v1_status",
        "status": "CAPPED_240_SECONDS",
        "protocol_sha256": sha(old),
        "source_sha256": record["source_sha256"],
        "stderr_sha256": sha(HERE / "census.stderr.txt"),
        "result_status": "empty_stdout_due_to_cap",
    }
    (HERE / "census_v1_status.json").write_text(json.dumps(failure, indent=2,
                                                        sort_keys=True) + "\n")
    record.update({
        "kind": "n131_d13_union_raw_cofactor_census_protocol_v2",
        "status": "FROZEN_AMENDED_BEFORE_CENSUS",
        "frozen_utc": datetime.now(timezone.utc).isoformat(),
        "amends_protocol_sha256": sha(old),
        "amendment_reason": "V1 reached its 240-second cap; use one subgroup-order product per selector and group-law-derived negative/image classes, with sampled direct checks.",
        "failed_attempt_status_sha256": sha(HERE / "census_v1_status.json"),
        "source_sha256": sha(HERE / "census.py"),
    })
    path = HERE / "protocol_v2.json"
    assert not path.exists()
    path.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    print(path)


def freeze_analysis():
    census = HERE / "census_result.json"
    assert json.loads(census.read_text())["status"] == "PASS_EXACT_POSITION_CENSUS"
    record = {
        "kind": "n131_d13_union_raw_class_convolution_protocol_v1",
        "status": "FROZEN_BEFORE_ANALYSIS",
        "frozen_utc": datetime.now(timezone.utc).isoformat(),
        "curve_id": json.loads(census.read_text())["curve_id"],
        "subgroup_order": "680564733841876926932320129493409985129",
        "census_result_sha256": sha(census),
        "source_sha256": sha(HERE / "analyze.py"),
        "summand_counts": [9, 10],
        "claim_boundary": "Exact ordered tuple counts by rational four-torsion class; conditional subgroup-uniform quotient is heuristic and is not observed relation yield.",
    }
    path = HERE / "analysis_protocol.json"
    assert not path.exists()
    path.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    print(path)


if __name__ == "__main__":
    {"census": freeze_census, "amend": freeze_amendment,
     "audit": freeze_audit, "analysis": freeze_analysis}[sys.argv[1]]()
