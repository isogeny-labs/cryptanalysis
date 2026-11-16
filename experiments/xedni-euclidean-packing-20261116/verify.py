"""Verify the checked Euclidean packing proof and exact lattice controls."""
import hashlib
import json
import re
import subprocess
from pathlib import Path

root = Path(__file__).resolve().parent
protocol = json.loads((root / "PROTOCOL.json").read_text())
assert protocol["schema"] == "xedni-euclidean-packing-protocol-v1"
subprocess.run(["python3", str(root / "run.py")], check=True, capture_output=True)
result = json.loads((root / "result.json").read_text())
assert result["schema"] == "xedni-euclidean-packing-control-v1"
rows = result["rows"]
assert len(rows) == 42
assert all(row["euclidean_bound_holds"] for row in rows)
assert all(not row["packing_certifies_collision"] or row["direct_collision"]
           for row in rows)
for t, first, count, box in ((1, 3, 127, 343), (2, 7, 1178, 3375)):
    first_row = next(row for row in rows if row["torsion_order"] == t
                     and row["packing_certifies_collision"])
    assert (first_row["K"], first_row["distinct_values"],
            first_row["coefficient_box"]) == (first, count, box)
formal = root / "formal"
deps = json.loads((root / "DEPENDENCIES.json").read_text())
assert (formal / "lean-toolchain").read_text().strip() == deps["lean_toolchain"]
assert f'rev = "{deps["mathlib_revision"]}"' in (formal / "lakefile.toml").read_text()
for name, digest in deps["imported_sources"].items():
    assert hashlib.sha256((root / name).read_bytes()).hexdigest() == digest
source = (formal / "EuclideanPacking.lean").read_text()
build = (formal / "build-output.txt").read_text()
assert "Build completed successfully (2704 jobs)." in build
assert "error:" not in build and "sorryAx" not in build
for file in (formal / "EuclideanPacking.lean", formal / "HeightPigeonhole.lean"):
    assert not re.search(r"\b(sorry|admit|sorryAx|native_decide)\b|^\s*axiom\s",
                         file.read_text())
names = re.findall(r"^#print axioms ([A-Za-z0-9_.]+)$", source, re.M)
assert len(names) == 6
for name in names:
    matches = re.findall(re.escape("'" + name + "'") +
                         r" depends on axioms: \[([^\]]+)\]", build, re.S)
    assert len(matches) == 1, name
    assert {part.strip() for part in matches[0].split(",")} <= {
        "propext", "Classical.choice", "Quot.sound"}, name
for line in (root / "SEAL.sha256").read_text().splitlines():
    digest, relative = line.split("  ", 1)
    assert hashlib.sha256((root / relative).read_bytes()).hexdigest() == digest, relative
print(json.dumps({"status": "PASS", "lean_declarations": len(names), "rows": len(rows)}))
