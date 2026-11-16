"""Verify sealed adaptive-stage Lean and exhaustive control evidence."""
import gzip
import hashlib
import json
from pathlib import Path

root = Path(__file__).resolve().parent
entries = (root / "SEAL.sha256").read_text().splitlines()
for line in entries:
    digest, name = line.split("  ", 1)
    assert hashlib.sha256((root / name).read_bytes()).hexdigest() == digest, name
for name, parent in (
    ("RandomLabelCoupling", "xedni-random-label-coupling-20261116"),
    ("SymbolicCollision", "xedni-symbolic-collision-bound-20261116"),
    ("LabelConditionedCollision", "xedni-label-conditioned-collision-20261116"),
    ("GroupTraceInvariant", "xedni-group-trace-invariant-20261116"),
    ("AdaptiveProgramInvariant", "xedni-adaptive-program-invariant-20261116"),
    ("TranscriptDeterminism", "xedni-transcript-determinism-20261116"),
    ("FirstCollisionLedger", "xedni-first-collision-ledger-20261116"),
    ("PrefixPatternBridge", "xedni-prefix-pattern-bridge-20261116"),
):
    path = root / "formal" / (name + ".lean")
    assert path.is_symlink()
    assert path.resolve() == (root.parent / parent / "formal" / (name + ".lean")).resolve()
protocol = json.loads((root / "protocol.json").read_text())
assert protocol["schema"] == "xedni-adaptive-stage-sum-protocol-v2"
assert json.loads((root / "protocol-v1.json").read_text())["schema"] == "xedni-adaptive-stage-sum-protocol-v1"
result = json.loads((root / "result.json").read_text())
audit = json.loads((root / "audit.json").read_text())
assert result["status"] == audit["status"] == "PASS"
assert result["initial_mass"] == 30240
assert result["total_hit_mass"] == 17640
assert result["terminal_live_mass"] == 12600
assert result["bucket_count"] == audit["rows_checked"] == 1932
assert audit["repeated_prefix_rows"] == 840
assert [s["bucket_count"] for s in result["stages"]] == [42,210,840,840]
assert [s["hit_mass"] for s in result["stages"]] == [7560,2520,0,7560]
assert [s["repeated_form_buckets"] for s in result["stages"]] == [0,0,0,840]
assert audit["result_sha256"] == hashlib.sha256((root / "result.json").read_bytes()).hexdigest()
raw = root / "buckets.jsonl.gz"
assert result["buckets_sha256"] == hashlib.sha256(raw.read_bytes()).hexdigest()
with gzip.open(raw, "rt") as stream:
    assert sum(1 for _ in stream) == 1932
pilot = json.loads((root / "pilot-result-v1.json").read_text())
assert result["stages"][:3] == pilot["stages"]
source = (root / "formal/AdaptiveStageSum.lean").read_text()
build = (root / "formal/build-output.txt").read_text()
assert "Build completed successfully (3146 jobs)." in build
names = ("liveSet", "hitSet", "live_step_partition", "live_hit_disjoint",
         "stop_flow", "stopped_mass_identity", "stage_bucket_mass_bound",
         "aggregate_bucket_bound")
for name in names:
    assert f"#print axioms {name}" in source
    lines = [line for line in build.splitlines() if f"'XedniAdaptiveStageSum.{name}'" in line]
    assert len(lines) == 1, name
    if "depends on axioms:" in lines[0]:
        axioms = lines[0].split("depends on axioms: [", 1)[1].split("]", 1)[0]
        assert set(axioms.split(", ")) <= {"propext", "Classical.choice", "Quot.sound"}, name
    else:
        assert "does not depend on any axioms" in lines[0], name
for banned in ("sorry", "admit", "sorryAx", "native_decide", "axiom "):
    assert banned not in source
print(json.dumps({"schema":"xedni-adaptive-stage-sum-verify-v1","status":"PASS",
                  "sealed_files":len(entries),"lean_declarations":len(names)},sort_keys=True))
