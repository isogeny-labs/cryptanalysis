"""Verify the finite-kernel Lean proof and exact group controls."""
import hashlib
import json
import re
import subprocess
from pathlib import Path

root = Path(__file__).resolve().parent
protocol = json.loads((root / "PROTOCOL.json").read_text())
assert protocol["schema"] == "xedni-finite-kernel-packing-protocol-v1"
subprocess.run(["python3", str(root / "run.py")], check=True, capture_output=True)
result = json.loads((root / "result.json").read_text())
assert result["schema"] == "xedni-finite-kernel-packing-control-v1"
rows = result["finite_kernel_rows"]
negative = result["omitted_kernel_counterexamples"]
assert len(rows) == 68 and len(negative) == 16
assert all(row["fiber_bound_holds"] and row["euclidean_bound_holds"] for row in rows)
assert all(not row["packing_certifies_collision"] or row["direct_collision"]
           for row in rows)
assert all(not row["false_fiber_bound"] for row in negative)
for t, k, count, box in ((1, 3, 127, 343), (2, 7, 1178, 3375),
                         (3, 11, 4167, 12167), (4, 15, 10108, 29791)):
    first = next(row for row in rows if row["kernel_card"] == t
                 and row["packing_certifies_collision"])
    assert (first["K"], first["distinct_values"], first["coefficient_box"],
            first["maximum_observed_fiber"]) == (k, count, box, t)
formal = root / "formal"
deps = json.loads((root / "DEPENDENCIES.json").read_text())
assert (formal / "lean-toolchain").read_text().strip() == deps["lean_toolchain"]
assert f'rev = "{deps["mathlib_revision"]}"' in (formal / "lakefile.toml").read_text()
for name, digest in deps["imported_sources"].items():
    assert hashlib.sha256((root / name).read_bytes()).hexdigest() == digest
source = (formal / "FiniteKernelPacking.lean").read_text()
build = (formal / "build-output.txt").read_text()
assert "Build completed successfully (2705 jobs)." in build
assert "error:" not in build and "sorryAx" not in build
for file in (formal / "FiniteKernelPacking.lean", formal / "EuclideanPacking.lean",
             formal / "HeightPigeonhole.lean"):
    assert not re.search(r"\b(sorry|admit|sorryAx|native_decide)\b|^\s*axiom\s",
                         file.read_text(), re.M)
names = re.findall(r"^#print axioms ([A-Za-z0-9_.]+)$", source, re.M)
assert len(names) == 3
for name in names:
    matches = re.findall(re.escape("'" + name + "'") +
                         r" depends on axioms: \[([^\]]+)\]", build, re.S)
    assert len(matches) == 1, name
    assert {part.strip() for part in matches[0].split(",")} <= {
        "propext", "Classical.choice", "Quot.sound"}, name
for line in (root / "SEAL.sha256").read_text().splitlines():
    digest, relative = line.split("  ", 1)
    assert hashlib.sha256((root / relative).read_bytes()).hexdigest() == digest, relative
print(json.dumps({"status": "PASS", "lean_declarations": len(names),
                  "finite_rows": len(rows), "counterexamples": len(negative)}))
