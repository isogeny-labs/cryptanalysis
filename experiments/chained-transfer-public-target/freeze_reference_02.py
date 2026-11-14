"""Development-only input inventory and byte hashing; no crypto arithmetic.

This regenerates a versioned manifest before a new source checkpoint/replay.
It is never invoked by the replay to replace its frozen expected hashes.
"""
from pathlib import Path
import hashlib
import json
import subprocess

repo = Path(__file__).resolve().parents[2]
study = Path(__file__).resolve().parent
prefix = study.relative_to(repo).as_posix()
old = repo / "experiments/chained-transfer-reference/evidence/g3-norm-primary-01/upstream-current-inputs.json"
root = json.loads(old.read_text())
assert len(root) == 343
entries = {"../crypto/" + path: digest for path, digest in root.items()}
pins = json.loads((study / "native/original/source-pins.json").read_text())
for name, entry in pins["files"].items():
    source = study / "native/original" / name
    assert hashlib.sha256(source.read_bytes()).hexdigest() == entry["sha256"]
    entries["../crypto/research/quartic_n4_la_20261021/" + name] = entry["sha256"]
selected = set(subprocess.check_output([
    "git", "ls-files", "--", "tools/lean", "tools/pcc", "pcc/keyring.json",
    prefix + "/native", prefix + "/formal",
], cwd=repo, text=True).splitlines())
for path in (study / "fixtures").rglob("*"):
    if path.is_file():
        selected.add(path.relative_to(repo).as_posix())
for folder in ["lean-bindings-01", "origin-lean-bindings-01"]:
    path = study / "evidence" / folder / "claims.json"
    selected.add(path.relative_to(repo).as_posix())
    selected.update(row["claim_path"] for row in json.loads(path.read_text()))
selected.update(prefix + "/" + name for name in [
    "check.sh", "replay_io.py", "freeze_reference.py", "freeze_reference_02.py", "upstream-commit.txt",
    "PROTOCOL-01.md", "DERIVATION.md", "PROOF_MAP.md",
    "evidence/primary-01/whole-parent-seven-jobs.yml",
])
selected.update([
    ".github/workflows/chained-transfer-reference.yml",
    ".github/workflows/chained-transfer-public-target.yml",
    ".github/workflows/pcc-gate.yml",
])
for relative in selected:
    entries[relative] = hashlib.sha256((repo / relative).read_bytes()).hexdigest()
(study / "reference-02.sha256").write_text("".join(
    digest + "  " + relative + "\n" for relative, digest in sorted(entries.items())
))
print(json.dumps({"root_inputs": 347, "consumer_inputs": len(selected),
                  "portable_inputs": len(entries), "manifest_self_excluded": True}))
