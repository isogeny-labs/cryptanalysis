#!/usr/bin/env bash
# Retrospective partial diagnosis; both original full acceptance gates stay failed.
set -u
[[ $# == 2 ]] || exit 2
expected=$1
out=$(realpath -m "$2")
[[ ! -e $out && $(git rev-parse HEAD) == "$expected" && -z $(git status --porcelain) ]] || exit 2
mkdir "$out"
trap 'status=$?; printf "%s\n" "$status" > "$out/orchestrator.exit"' EXIT
cp "$0" "$out/original-command.sh"
bash scripts/checkpoint.sh gate > "$out/immediate-original-gate.txt" 2>&1
status=$?
printf '%s\n' "$status" > "$out/immediate-original-gate.exit"
[[ $status == 0 ]] || exit "$status"
root=/workspace/scratch/ct80-observer-validation-04
old=/workspace/scratch/ct75-norm-arithmetic-panels-01
build=/workspace/scratch/ct80-observer-partial-parity-build-04
python3 - "$out" "$build" <<'PY'
from pathlib import Path
import hashlib,json,shutil,sys
out,build=map(Path,sys.argv[1:]);assert(build/'compile.exit').read_text().strip()=='0';rows=[json.loads(x) for x in(build/'compile.jsonl').read_text().splitlines()];bins=[x for x in rows if x.get('reason')=='compiler-artifact' and x.get('executable')];assert len(bins)==1
row=bins[0];p=Path(row['executable']);dest=out/'actual-partial-parity.bin';shutil.copy2(p,dest)
source=Path('/workspace/cryptanalysis/experiments/chained-transfer-public-target/norm-arithmetic-storage-02/parity-compare/src/bin/observed_partial.rs');assert source.read_bytes()==(build/'actual-source.rs').read_bytes()
(out/'partial-compiler-runtime-custody.json').write_text(json.dumps(dict(Cargo_artifact=row,actual_copy=str(dest),bytes=dest.stat().st_size,sha256=hashlib.sha256(dest.read_bytes()).hexdigest(),source_sha256=hashlib.sha256(source.read_bytes()).hexdigest()),indent=2)+'\n')
original=Path('/workspace/scratch/ct75-norm-arithmetic-partial-analysis-01/actual-analyzer.bin');held=json.loads(Path('/workspace/scratch/ct77-whole-model-and-third-handoff-18/current-inputs.json').read_text());entry=held[str(original)];assert (entry if isinstance(entry,str) else entry['sha256'])==hashlib.sha256(original.read_bytes()).hexdigest()
shutil.copy2(original,out/'actual-original-partial-analyzer.bin');(out/'original-partial-analyzer-custody.json').write_text(json.dumps(dict(original=str(original),held_original_entry=entry,actual_copy=str(out/'actual-original-partial-analyzer.bin'),whole_bytes_equal=True),indent=2)+'\n')
PY
status=$?
printf '%s\n' "$status" > "$out/compiler-runtime-custody.exit"
[[ $status == 0 ]] || exit "$status"
timeout 120 "$out/actual-original-partial-analyzer.bin" "$root/panels" "$root/cases60.json" "$out/actual-partial-vectors.json" > "$out/original-partial-analysis.txt" 2>&1
status=$?
printf '%s\n' "$status" > "$out/original-partial-analysis.exit"
[[ $status == 0 ]] || exit "$status"
timeout 120 "$out/actual-partial-parity.bin" --old-parity "$old" "$root/panels" "$out/actual-partial-old-whole-parity.json" > "$out/whole-old-parity.txt" 2>&1
status=$?
printf '%s\n' "$status" > "$out/whole-old-parity.exit"
[[ $status == 0 ]] || exit "$status"
python3 - "$root/panels" "$out/actual-whole-packet-omission" <<'PY'
from pathlib import Path
import sys
src,dest=map(Path,sys.argv[1:]);dest.mkdir()
for p in src.iterdir():
 if p.is_file():(dest/p.name).symlink_to(p)
target=dest/'reused-direct.txt';target.unlink();lines=(src/'reused-direct.txt').read_bytes().splitlines(keepends=True);actual=[line for line in lines if b'N4_NORM_ARITHMETIC_CASE ' in line];assert len(actual)==1;target.write_bytes(b''.join(line for line in lines if b'N4_NORM_ARITHMETIC_CASE ' not in line))
PY
timeout 120 "$out/actual-partial-parity.bin" --old-parity "$old" "$out/actual-whole-packet-omission" "$out/invalid-omission-accepted.json" > "$out/whole-packet-omission.txt" 2>&1
status=$?
printf '%s\n' "$status" > "$out/whole-packet-omission.exit"
[[ $status == 101 && ! -e $out/invalid-omission-accepted.json ]] || exit 1
