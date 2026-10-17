"""Freeze the W23 sample-edge and source-rank projection."""
import hashlib
import json
from pathlib import Path


D = Path(__file__).resolve().parent
ROOT = D.parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


sources = ["n131_w23_sixpair_density_20261016/run_result.json",
           "n131_w23_sixpair_density_20261016/audit_result.json",
           "n131_w23_sixpair_density_20261016/protocol.json"]
record = {"schema": 1,
          "runner_sha256": sha(D / "n131_leaf_projection_sage.py"),
          "runtime_info_sha256": sha(D / "sage_runtime_info.json"),
          "sources": {name: sha(ROOT / name) for name in sources},
          "worker_count": 1,
          "input_law": "all eight archived W23 sample edges with four sign combinations each"}
(D / "n131_leaf_projection_protocol.json").write_text(json.dumps(record, sort_keys=True, indent=2) + "\n")
print(sha(D / "n131_leaf_projection_protocol.json"))
