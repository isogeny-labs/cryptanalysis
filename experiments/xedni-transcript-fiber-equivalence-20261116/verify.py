"""Verify sealed adaptive transcript-fiber theorem and exhaustive census."""
import gzip
import hashlib
import json
import re
from pathlib import Path

root = Path(__file__).resolve().parent
entries = (root / "SEAL.sha256").read_text().splitlines()
for line in entries:
    digest, name = line.split("  ",1)
    assert hashlib.sha256((root/name).read_bytes()).hexdigest() == digest, name
for name,parent in (
    ("RandomLabelCoupling","xedni-random-label-coupling-20261116"),
    ("SymbolicCollision","xedni-symbolic-collision-bound-20261116"),
    ("LabelConditionedCollision","xedni-label-conditioned-collision-20261116"),
    ("GroupTraceInvariant","xedni-group-trace-invariant-20261116"),
    ("AdaptiveProgramInvariant","xedni-adaptive-program-invariant-20261116"),
    ("TranscriptDeterminism","xedni-transcript-determinism-20261116"),
    ("FirstCollisionLedger","xedni-first-collision-ledger-20261116"),
    ("PrefixPatternBridge","xedni-prefix-pattern-bridge-20261116"),
    ("AdaptiveStageSum","xedni-adaptive-stage-sum-20261116"),
):
    path = root/"formal"/(name+".lean")
    assert path.is_symlink()
    assert path.resolve() == (root.parent/parent/"formal"/(name+".lean")).resolve()
protocol = json.loads((root/"protocol.json").read_text())
assert protocol["schema"] == "xedni-transcript-fiber-equivalence-protocol-v1"
result = json.loads((root/"result.json").read_text())
audit = json.loads((root/"audit.json").read_text())
assert result["status"] == audit["status"] == "PASS"
assert result["fiber_cells_checked"] == 823543
assert result["positive_fiber_cells"] == audit["positive_fibers_checked"] == 8820
assert result["zero_fiber_cells"] == 814723
assert result["total_execution_pairs"] == audit["total_weight"] == 35280
assert result["fiber_count_mismatches"] == 0
assert audit["result_sha256"] == hashlib.sha256((root/"result.json").read_bytes()).hexdigest()
raw = root/"positive-fibers.jsonl.gz"
assert result["positive_rows_sha256"] == hashlib.sha256(raw.read_bytes()).hexdigest()
with gzip.open(raw,"rt") as stream:
    assert sum(1 for _ in stream) == 8820
source = (root/"formal/TranscriptFiberEquivalence.lean").read_text()
build = (root/"formal/build-output.txt").read_text()
assert "Build completed successfully (3147 jobs)." in build
names = ("formsFromTranscript_prefix","labels_of_symbolic_fiber",
         "labels_iff_symbolic_fiber","dlp_labels_iff_symbolic_fiber",
         "actualFiberCount","symbolicFiberCount","encodingCount",
         "actual_fiber_count_eq_symbolic","actual_fiber_partition")
for name in names:
    assert f"#print axioms {name}" in source
    prefix = re.escape("'XedniTranscriptFiberEquivalence."+name+"'")
    matches = re.findall(prefix+r" depends on axioms: \[([^\]]+)\]",build,re.S)
    if matches:
        assert len(matches) == 1, name
        assert set(x.strip() for x in matches[0].split(",")) <= {
            "propext","Classical.choice","Quot.sound"}, name
    else:
        assert len(re.findall(prefix+r" does not depend on any axioms",build)) == 1, name
for banned in ("sorry","admit","sorryAx","native_decide","axiom "):
    assert banned not in source
print(json.dumps({"schema":"xedni-transcript-fiber-equivalence-verify-v1",
                  "status":"PASS","sealed_files":len(entries),
                  "lean_declarations":len(names)},sort_keys=True))
