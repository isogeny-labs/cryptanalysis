"""Verify the height-growth proof, censored arm, and amended exact panel."""
import hashlib
import gzip
import json
import re
import subprocess
from pathlib import Path

root = Path(__file__).resolve().parent
v1 = json.loads((root / "PROTOCOL.json").read_text())
v2 = json.loads((root / "PROTOCOL-v2.json").read_text())
attempts = json.loads((root / "attempts.json").read_text())["attempts"]
assert v1["schema"] == "xedni-height-growth-obstruction-protocol-v1"
assert v2["schema"] == "xedni-height-growth-obstruction-protocol-v2"
assert v1["n_panel"] == v2["n_panel"] == [1, 2, 3, 5, 8, 13, 21, 34]
assert attempts[0]["status"] == "interrupted_resource_cost"
assert attempts[0]["rows_written"] == 0
assert (root / "initial-run.stdout").read_bytes() == b""
assert "KeyboardInterrupt" in gzip.decompress(
    (root / "initial-run.stderr.gz").read_bytes()).decode()
assert attempts[1]["status"] == "PASS" and attempts[1]["rows_written"] == 95
runtime1 = json.loads((root / "sage-runtime-info.json").read_text())
runtime2 = json.loads((root / "sage-runtime-info-v2.json").read_text())
assert runtime1["status"] == runtime2["status"] == "verified"
assert runtime1["manifest_sha256"] == runtime2["manifest_sha256"]
sage = "/Volumes/SSD990/cryptanalysis/sage"
for script, stdout_file, stderr_file in (
    ("run-v2.py", "run-v2.stdout", "run-v2.stderr"),
    ("audit.py", "audit.stdout", "audit.stderr"),
):
    replay = subprocess.run([sage, "-python", str(root / script)],
                            capture_output=True, check=True)
    assert replay.stdout == (root / stdout_file).read_bytes()
    assert replay.stderr == (root / stderr_file).read_bytes() == b""
result = json.loads((root / "result.json").read_text())
assert result["schema"] == "xedni-height-growth-obstruction-result-v2"
assert result["rank"] == result["torsion_order"] == 1
assert result["generator_match_up_to_sign"]
assert len(result["panel"]) == 8
assert sum(len(case["rows"]) for case in result["panel"]) == 95
for case in result["panel"]:
    n = case["n"]
    assert case["first_collision_K"] == (n + 1) // 2
    assert case["first_packing_K"] == n
    assert case["minimum_nonzero_relation_max_coefficient"] == n
formal = root / "formal"
deps = json.loads((root / "DEPENDENCIES.json").read_text())
assert (formal / "lean-toolchain").read_text().strip() == deps["lean_toolchain"]
assert f'rev = "{deps["mathlib_revision"]}"' in (formal / "lakefile.toml").read_text()
source = (formal / "HeightGrowthObstruction.lean").read_text()
build = (formal / "build-output.txt").read_text()
assert "Build completed successfully (9040 jobs)." in build
assert "error:" not in build and "sorryAx" not in build
assert not re.search(r"\b(sorry|admit|sorryAx|native_decide)\b|^\s*axiom\s",
                     source, re.M)
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
print(json.dumps({"status": "PASS", "lean_declarations": len(names),
                  "n_cases": 8, "rows": 95, "censored_arms": 1}))
