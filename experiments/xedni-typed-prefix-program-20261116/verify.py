"""Verify sealed typed prefix theorem and exhaustive finite control."""
import gzip
import hashlib
import json
import re
from pathlib import Path

root=Path(__file__).resolve().parent
entries=(root/"SEAL.sha256").read_text().splitlines()
for line in entries:
    digest,name=line.split("  ",1)
    assert hashlib.sha256((root/name).read_bytes()).hexdigest()==digest,name
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
    ("TranscriptFiberEquivalence","xedni-transcript-fiber-equivalence-20261116"),
):
    path=root/"formal"/(name+".lean")
    assert path.is_symlink()
    assert path.resolve()==(root.parent/parent/"formal"/(name+".lean")).resolve()
protocol=json.loads((root/"protocol.json").read_text())
assert protocol["schema"]=="xedni-typed-prefix-program-protocol-v1"
result=json.loads((root/"result.json").read_text())
audit=json.loads((root/"audit.json").read_text())
assert result["status"]==audit["status"]=="PASS"
assert result["complete_label_tuples_checked"]==117649
assert result["form_causality_checks"]==588245
assert result["group_prefix_checks"]==176400
assert result["fiber_cells_checked"]==960743
assert result["positive_fiber_cells"]==audit["positive_fibers_checked"]==17437
assert result["zero_fiber_cells"]==943306
assert result["mismatches"]==0
assert audit["weight_per_length"]==35280
assert audit["result_sha256"]==hashlib.sha256((root/"result.json").read_bytes()).hexdigest()
raw=root/"positive-prefix-fibers.jsonl.gz"
assert result["positive_rows_sha256"]==hashlib.sha256(raw.read_bytes()).hexdigest()
with gzip.open(raw,"rt") as stream:
    assert sum(1 for _ in stream)==17437
source=(root/"formal/TypedPrefixProgram.lean").read_text()
build=(root/"formal/build-output.txt").read_text()
assert "Build completed successfully (3148 jobs)." in build
names=("takeAt","runGroup_takeAt","restrictLabels",
       "formsFromTranscript_takeAt","dlp_prefix_labels_iff_symbolic",
       "form_prefix_depends_only_on_visible_labels",
       "prefixSymbolicFiberCount","actual_prefix_fiber_count_eq_symbolic")
for name in names:
    assert f"#print axioms {name}" in source
    prefix=re.escape("'XedniTypedPrefixProgram."+name+"'")
    matches=re.findall(prefix+r" depends on axioms: \[([^\]]+)\]",build,re.S)
    if matches:
        assert len(matches)==1,name
        assert set(x.strip() for x in matches[0].split(",")) <= {
            "propext","Classical.choice","Quot.sound"},name
    else:
        assert len(re.findall(prefix+r" does not depend on any axioms",build))==1,name
for banned in ("sorry","admit","sorryAx","native_decide","axiom "):
    assert banned not in source
print(json.dumps({"schema":"xedni-typed-prefix-program-verify-v1","status":"PASS",
                  "sealed_files":len(entries),"lean_declarations":len(names)},sort_keys=True))
