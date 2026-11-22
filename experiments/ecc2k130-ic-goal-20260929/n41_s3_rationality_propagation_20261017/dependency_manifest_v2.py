"""Extend the post-run source readback to loaded codegen and fourmul modules."""
import hashlib
import json
from pathlib import Path


D = Path(__file__).resolve().parent
WORKSPACE = D.parents[2]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


old = json.loads((D / "dependency_manifest.json").read_text())
extra = [
    "ecc2k130/codegen/build.py",
    "ecc2k130/codegen/ir.py",
    "experiments/ecc2k130-ic-goal-20260929/n131_reciprocal_s3_fourmul_20261010/fourmul.py",
]
record = dict(old)
record.update({"schema": 2,
               "supersedes_manifest_sha256": sha(D / "dependency_manifest.json"),
               "workspace_sources": {name: sha(WORKSPACE / name) for name in extra},
               "producer_v2_sha256": sha(Path(__file__))})
(D / "dependency_manifest_v2.json").write_text(json.dumps(record, sort_keys=True, indent=2) + "\n")
print(sha(D / "dependency_manifest_v2.json"))
