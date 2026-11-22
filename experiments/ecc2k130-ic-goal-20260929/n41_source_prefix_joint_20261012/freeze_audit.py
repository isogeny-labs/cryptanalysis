"""Bind source, hits, checked Sage runtime, and independent replay code."""

import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
GOAL = HERE.parent
SOURCE = GOAL / "n131_w18_allseed_fourpair_20261012/n41_diagonal"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


joins = json.loads((HERE / "join_summary.json").read_text())
paths = [HERE / "audit_sage.py", HERE / "panel.json", HERE / "analysis.json",
         HERE / "join_protocol.json", HERE / "join_summary.json",
         HERE / "sage_runtime_info.json", SOURCE / "pairs.tsv",
         SOURCE / "control_fixture.json", SOURCE / "audit_result.json",
         GOAL / "n41_w7_entropy_cubic_20261011/w8/geometry.json"]
for name in ("n41_w8_sixpair_mitm_20261011", "n41_w8_ninepair_join_control_20261012",
             "n41_w8_tenpair_xquotient_20261012"):
    paths.append(GOAL / name / "audit_result.json")
for receipt in joins["receipts"]:
    if receipt["status"] == "HIT_PENDING_SAGE":
        label = receipt["label"]
        paths.extend((HERE / f"{label}.join.receipt.json",
                      HERE / f"{label}.join.stdout", HERE / f"{label}.join.stderr"))
result = {"status": "FROZEN_BEFORE_N41_PREFIX_SAGE_REPLAY",
          "candidate_id": None, "sources": {str(path): sha(path) for path in paths}}
with (HERE / "audit_protocol.json").open("x") as out:
    json.dump(result, out, sort_keys=True, indent=2)
    out.write("\n")
