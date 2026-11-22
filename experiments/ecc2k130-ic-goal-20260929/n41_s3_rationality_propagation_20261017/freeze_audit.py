"""Bind the independent Sage leaf-support audit before its execution."""
import hashlib
import json
from pathlib import Path


D = Path(__file__).resolve().parent
ROOT = D.parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


sources = [
    "n41_w8_fixed_sum_table_20261009/geometry.json",
    "n41_w7_entropy_cubic_20261011/w8/geometry.json",
    "n41_sixpair_shared_target_20261017/join_audit_result.json",
]
record = {"schema": 1,
          "auditor_sha256": sha(D / "audit_leaf_sage.py"),
          "runtime_info_sha256": sha(D / "sage_runtime_info.json"),
          "formula_sha256": sha(D / "public.xcnf"),
          "sources": {name: sha(ROOT / name) for name in sources}}
(D / "audit_protocol.json").write_text(json.dumps(record, sort_keys=True, indent=2) + "\n")
print(sha(D / "audit_protocol.json"))
