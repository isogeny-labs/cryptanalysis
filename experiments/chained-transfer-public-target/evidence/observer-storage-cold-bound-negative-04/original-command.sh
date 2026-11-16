#!/usr/bin/env bash
# Resume only unrun observer controls/panels; preserve passing four-test parity.
set -u
[[ $# == 6 ]] || exit 2
layout=$(realpath "$1")
build=$(realpath "$2")
previous=$(realpath "$3")
controls=$(realpath "$4")
out=$(realpath -m "$5")
expected=$6
source=$(cd -- "$(dirname -- "$0")" && pwd -P)
study=experiments/chained-transfer-public-target
[[ ! -e $out && $(git rev-parse HEAD) == "$expected" && -z $(git status --porcelain) ]] || exit 2
export PATH="$HOME/.cargo/bin:$PATH"
export RUSTUP_TOOLCHAIN=1.99.1
export CARGO_TARGET_DIR=/workspace/scratch/ct80-observer-storage-build-02-cache
mkdir "$out"
cp "$0" "$out/original-command.sh"
trap 'status=$?; printf "%s\n" "$status" > "$out/orchestrator.exit"; date -u +%FT%TZ > "$out/finish.txt"' EXIT
date -u +%FT%TZ > "$out/start.txt"
bash scripts/checkpoint.sh gate > "$out/immediate-original-gate.txt" 2>&1
status=$?
printf '%s\n' "$status" > "$out/immediate-original-gate.exit"
[[ $status == 0 ]] || exit "$status"
python3 - "$source" "$layout" "$build" "$previous" "$out" <<'CUSTODY'
from pathlib import Path
import hashlib,json,shutil,sys
source,layout,build,previous,out=map(Path,sys.argv[1:])
for label in ['math-native','math-whole-compare','math-runtime-custody']:
 assert(previous/(label+'.exit')).read_text().strip()=='0',label
assert(previous/'primitive-native.exit').read_text().strip()=='126'
assert(source/'taps/src/lib.rs').read_bytes()==(layout/'derived-layout/n4-arithmetic-taps/src/lib.rs').read_bytes()
assert(source/'frontend/src/bin/analyze.rs').read_bytes()==(layout/'derived-layout/norm-census/src/bin/analyze.rs').read_bytes()
rows=json.loads((build/'actual-executables-supplement.json').read_text());copies=[]
for row in rows:
 p=Path(row['Cargo_artifact']['executable']);name='actual-census-executable.bin' if row['Cargo_artifact']['target']['name']=='norm-halving-arithmetic-census' else 'actual-unchanged-full-analyzer.bin';q=out/name
 assert hashlib.sha256(p.read_bytes()).hexdigest()==row['sha256'] and p.read_bytes()==Path(row['actual_copy']).read_bytes()
 shutil.copy2(p,q);assert q.stat().st_mode & 0o111
 copies.append(dict(**row,resumed_copy=str(q),actual_mode_preserved=True))
(out/'resumed-executable-custody.json').write_text(json.dumps(copies,indent=2)+'\n')
(out/'prior-passing-math-custody.json').write_text(json.dumps({p.name:dict(bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in sorted(previous.iterdir()) if p.is_file() and p.suffix!='.bin'},indent=2)+'\n')
files=[p for p in sorted((layout/'derived-layout').rglob('*')) if p.is_file()];(out/'frozen-derived-source.sha256').write_text(''.join(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+str(p)+'\n' for p in files))
CUSTODY
status=$?
printf '%s\n' "$status" > "$out/resumed-executable-custody.exit"
[[ $status == 0 ]] || exit "$status"
python3 - "$controls" <<'CONTROLS'
from pathlib import Path
import sys
p=Path(sys.argv[1])
for label,expected in [('primitive-native',0),('disabled-native',2),('FpR-omission-caller',0),('quadratic-omission-caller',0)]:assert(p/(label+'.exit')).read_text().strip()==str(expected)
for family in ['actual-FpR-omission','actual-quadratic-omission']:
 for arm,expected in [('positive',0),('negative',101)]:assert(p/family/(arm+'-native.exit')).read_text().strip()==str(expected)
assert not(p/'panels/cold-panel.exit').exists()
CONTROLS
status=$?
printf '%s\n' "$status" > "$out/prior-passing-controls.exit"
[[ $status == 0 ]] || exit "$status"
sha256sum --check "$controls/frozen-derived-source.sha256" > "$out/interruption-source-guards.txt" 2>&1
status=$?
printf '%s\n' "$status" > "$out/interruption-source-guards.exit"
[[ $status == 0 ]] || exit "$status"
xz -dc "$source/cases60.json.xz" > "$out/cases60.json"
"$out/actual-unchanged-full-analyzer.bin" "$controls/panels" "$out/cases60.json" "$out/invalid-interrupted-accepted.json" > "$out/interruption-full-analysis.txt" 2>&1
status=$?
printf '%s\n' "$status" > "$out/interruption-full-analysis.exit"
[[ $status == 101 && ! -e $out/invalid-interrupted-accepted.json ]] || exit 1
xz -dc "$source/cases60.json.xz" > "$out/cases60.json"
bash "$source/run-panels.sh" "$out/actual-census-executable.bin" "$out/cases60.json" "$out/panels" > "$out/full-panel-caller.txt" 2>&1
panel=$?
printf '%s\n' "$panel" > "$out/full-panel-caller.exit"
"$out/actual-unchanged-full-analyzer.bin" "$out/panels" "$out/cases60.json" "$out/accepted-full-analysis.json" > "$out/full-analysis-caller.txt" 2>&1
analysis=$?
printf '%s\n' "$analysis" > "$out/full-analysis-caller.exit"
old=/workspace/scratch/ct75-norm-arithmetic-panels-01
comparator=/workspace/scratch/ct79-observer-parity-build-01/actual-comparator.bin
"$comparator" --old-parity "$old" "$out/panels" "$out/accepted-old-whole-parity.json" > "$out/old-parity-caller.txt" 2>&1
parity=$?
printf '%s\n' "$parity" > "$out/old-parity-caller.exit"
if [[ $panel == 0 && $analysis == 0 && $parity == 0 ]]; then
 python3 - "$out" <<'PY'
from pathlib import Path
import json,sys
o=Path(sys.argv[1]);src=o/'panels';dst=o/'actual-whole-packet-omission';dst.mkdir()
for p in sorted(src.iterdir()):
 if p.is_file(): (dst/p.name).symlink_to(p)
victim=dst/'reused-direct.txt';victim.unlink();lines=(src/'reused-direct.txt').read_bytes().splitlines(keepends=True);omitted=[x for x in lines if b'N4_NORM_ARITHMETIC_CASE ' in x];assert len(omitted)==1
victim.write_bytes(b''.join(x for x in lines if b'N4_NORM_ARITHMETIC_CASE ' not in x));(o/'whole-packet-omission.json').write_text(json.dumps(dict(actual_file=str(src/'reused-direct.txt'),complete_packet_lines_removed=1,other_files='transparent exact original links; all actual exit files unchanged',accepted_output='must not exist'),indent=2)+'\n')
PY
 "$comparator" --old-parity "$old" "$out/actual-whole-packet-omission" "$out/invalid-omission-accepted.json" > "$out/whole-packet-omission-caller.txt" 2>&1
 omission=$?
 printf '%s\n' "$omission" > "$out/whole-packet-omission-caller.exit"
 [[ $omission == 101 && ! -e $out/invalid-omission-accepted.json ]] || exit 1
fi
(cd "$layout/original-layout" && sha256sum --check "$layout/original-785.sha256") > "$out/final-original-785.txt" 2>&1
guards=$?
printf '%s\n' "$guards" > "$out/final-original-785.exit"
[[ $guards == 0 ]] || exit "$guards"
sha256sum --check "$out/frozen-derived-source.sha256" > "$out/final-derived-source.txt" 2>&1
status=$?
printf '%s\n' "$status" > "$out/final-derived-source.exit"
[[ $status == 0 ]] || exit "$status"
[[ $panel == 0 && $analysis == 0 && $parity == 0 ]] || exit 1
exit 0
