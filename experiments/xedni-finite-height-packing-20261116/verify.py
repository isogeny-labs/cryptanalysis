"""Verify pinned finite-grid proof receipts and exact lattice controls."""
import hashlib
import json
import re
import subprocess
from pathlib import Path

root = Path(__file__).resolve().parent
protocol = json.loads((root / "PROTOCOL.json").read_text())
assert protocol["schema"] == "xedni-finite-height-packing-protocol-v1"
subprocess.run(["python3", str(root / "run.py")], check=True, capture_output=True)
rows = json.loads((root / "result.json").read_text())["rows"]
assert len(rows) == 34
assert all(row["count_within_packing_bound"] for row in rows)
assert all(not row["packing_certifies_collision"] or row["direct_collision"] for row in rows)
for t, first in ((1, 5), (2, 12)):
    assert min(row["K"] for row in rows if row["torsion_order"] == t
               and row["packing_certifies_collision"]) == first
formal = root / "formal"
assert (formal / "lean-toolchain").read_text().strip() == "leanprover/lean4:v4.35.0-rc4"
assert 'rev = "021c46bdd042f67b538b9f9871d556a93713a9a9"' in (formal / "lakefile.toml").read_text()
source = (formal / "FiniteGridPacking.lean").read_text()
build = (formal / "build-output.txt").read_text()
assert "Build completed successfully (1445 jobs)." in build
assert "error:" not in build and "sorryAx" not in build
assert not re.search(r"\b(sorry|admit|sorryAx|native_decide|axiom)\b", source)
names = re.findall(r"^#print axioms ([A-Za-z0-9_.]+)$", source, re.M)
assert len(names) == 3
for name in names:
    pattern = re.escape("'" + name + "'") + r" depends on axioms: \[([^\]]+)\]"
    matches = re.findall(pattern, build, re.S)
    assert len(matches) == 1, name
    assert {s.strip() for s in matches[0].split(",")} <= {
        "propext", "Classical.choice", "Quot.sound"}, name
for line in (root / "SEAL.sha256").read_text().splitlines():
    digest, relative = line.split("  ", 1)
    assert hashlib.sha256((root / relative).read_bytes()).hexdigest() == digest, relative
print(json.dumps({"status": "PASS", "lean_declarations": len(names), "rows": len(rows)}))
