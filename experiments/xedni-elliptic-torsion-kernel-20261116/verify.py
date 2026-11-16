"""Verify Lean receipts and independently replay the rational-curve control."""
import hashlib
import json
import re
import subprocess
from pathlib import Path

root = Path(__file__).resolve().parent
protocol = json.loads((root / "PROTOCOL.json").read_text())
assert protocol["schema"] == "xedni-elliptic-torsion-kernel-protocol-v1"
sage = "/Volumes/SSD990/cryptanalysis/sage"
runtime = json.loads((root / "sage-runtime-info.json").read_text())
assert runtime["status"] == "verified" and runtime["manifest_sha256"]
for script, stdout_file, stderr_file in (
    ("curve_control.py", "curve-control.stdout", "curve-control.stderr"),
    ("audit.py", "audit.stdout", "audit.stderr"),
):
    replay = subprocess.run([sage, "-python", str(root / script)],
                            capture_output=True, check=True)
    assert replay.stdout == (root / stdout_file).read_bytes()
    assert replay.stderr == (root / stderr_file).read_bytes() == b""
data = json.loads((root / "curve-result.json").read_text())
assert data["schema"] == "xedni-elliptic-torsion-curve-control-v1"
assert data["rank"] == data["torsion_order"] == 1
assert data["point_is_generator_up_to_sign"]
assert len(data["rows"]) == 5
assert data["rows"][1]["packing_certifies_collision"]
formal = root / "formal"
deps = json.loads((root / "DEPENDENCIES.json").read_text())
assert (formal / "lean-toolchain").read_text().strip() == deps["lean_toolchain"]
assert f'rev = "{deps["mathlib_revision"]}"' in (formal / "lakefile.toml").read_text()
for name, digest in deps["imported_sources"].items():
    assert hashlib.sha256((root / name).read_bytes()).hexdigest() == digest
source = (formal / "EllipticTorsionKernel.lean").read_text()
build = (formal / "build-output.txt").read_text()
assert "Build completed successfully (3507 jobs)." in build
assert "error:" not in build and "sorryAx" not in build
for file in (formal / "EllipticTorsionKernel.lean",
             formal / "FiniteKernelPacking.lean",
             formal / "EuclideanPacking.lean",
             formal / "HeightPigeonhole.lean"):
    assert not re.search(r"\b(sorry|admit|sorryAx|native_decide)\b|^\s*axiom\s",
                         file.read_text(), re.M)
names = re.findall(r"^#print axioms ([A-Za-z0-9_.]+)$", source, re.M)
assert len(names) == 4
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
                  "rational_curve_rows": len(data["rows"])}))
