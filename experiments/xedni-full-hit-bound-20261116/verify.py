"""Verify the sealed full-hit Lean proof and exact group-label controls."""
import hashlib
import json
import re
from pathlib import Path

root = Path(__file__).resolve().parent
entries = (root / "SEAL.sha256").read_text().splitlines()
for entry in entries:
    digest, name = entry.split("  ", 1)
    assert hashlib.sha256((root / name).read_bytes()).hexdigest() == digest, name
protocol = json.loads((root / "protocol.json").read_text())
result = json.loads((root / "result.json").read_text())
assert protocol["schema"] == "xedni-full-hit-bound-protocol-v1"
assert result["schema"] == "xedni-full-hit-bound-result-v1"
assert result["status"] == "PASS"
assert result["z7"]["executions"] == 35280
assert result["z7"]["first_hit_counts"] == {
    "1": 5040, "2": 7560, "3": 2520, "5": 7560, "survived": 12600}
assert result["z7"]["total_hit"] == 22680
assert result["z101"]["hit_probability"] == "5/202"
assert len(result["z101"]["nonzero_case_rows"]) == 4
assert int(result["z101"]["bound_left"]) <= int(result["z101"]["bound_right"])
source = (root / "formal/FullHitBound.lean").read_text()
build = (root / "formal/build-output.txt").read_text()
assert "Build completed successfully (3154 jobs)." in build
for bad in ("sorry", "admit", "sorryAx", "native_decide", "axiom "):
    assert bad not in source
assert "sorryAx" not in build and "error:" not in build
names = re.findall(r"^#print axioms (\w+)$", source, re.M)
assert len(names) == 7
for name in names:
    prefix = re.escape("'XedniFullHitBound." + name + "'")
    matches = re.findall(prefix + r" depends on axioms: \[([^\]]+)\]", build, re.S)
    if matches:
        assert len(matches) == 1, name
        assert {a.strip() for a in matches[0].split(",")} <= {
            "propext", "Classical.choice", "Quot.sound"}, name
    else:
        assert len(re.findall(prefix + r" does not depend on any axioms", build)) == 1, name
print(json.dumps({"status": "PASS", "sealed_files": len(entries),
                  "lean_declarations": len(names), "z7_executions": 35280,
                  "z101_hit_probability": "5/202"}, sort_keys=True))
