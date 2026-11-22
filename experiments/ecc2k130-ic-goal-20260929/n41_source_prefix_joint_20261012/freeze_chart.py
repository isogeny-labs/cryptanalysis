"""Freeze the independent checked-Sage chart audit inputs."""

import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


paths = [HERE / "chart_sage.py", HERE / "sage_audit_result.json",
         HERE / "sage_runtime_info.json", HERE / "audit_protocol.json"]
result = {"status": "FROZEN_BEFORE_N41_S3_CHART_REPLAY",
          "sources": {str(path): sha(path) for path in paths}}
with (HERE / "chart_protocol.json").open("x") as out:
    json.dump(result, out, sort_keys=True, indent=2)
    out.write("\n")
