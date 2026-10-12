"""Freeze positive-chart Sage-audit inputs before execution."""

import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
GOAL = HERE.parent


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


paths = (HERE / "audit_sage.py", HERE / "positive_chart.json",
         HERE / "sage_runtime_info.json",
         GOAL / "n41_w8_sixpair_mitm_20261011/join_input.tsv",
         GOAL / "n41_w8_tenpair_density_control_20261012/audit_result.json")
record = {"status": "FROZEN_BEFORE_FUNCTIONAL_CHART_SAGE_AUDIT",
          "sources": {str(path): sha(path) for path in paths}}
with (HERE / "audit_protocol.json").open("x") as stream:
    json.dump(record, stream, indent=2, sort_keys=True)
    stream.write("\n")
