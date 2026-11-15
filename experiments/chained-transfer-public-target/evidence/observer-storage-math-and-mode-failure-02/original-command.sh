#!/usr/bin/env bash
set -u
export PATH="$HOME/.cargo/bin:$PATH"
export RUSTUP_TOOLCHAIN=1.99.1
export CARGO_TARGET_DIR=/workspace/scratch/ct80-observer-storage-build-02-cache
layout=/workspace/scratch/ct80-observer-storage-layout-02
out=/workspace/scratch/ct80-observer-validation-02
study=experiments/chained-transfer-public-target
source=/workspace/cryptanalysis/$study/norm-arithmetic-storage-02
math=$layout/derived-layout/cryptanalysis/$study/norm-halving-evaluator
build=/workspace/scratch/ct80-observer-storage-build-02
[[ ! -e $out && $(git rev-parse HEAD) == b4e3543018ddc5ed70a34ee17280f23b8848484c && -z $(git status --porcelain) ]] || exit 2
mkdir "$out"
cp "$0" "$out/original-command.sh"
bash scripts/checkpoint.sh gate > "$out/immediate-original-gate.txt" 2>&1
status=$?
printf '%s\n' "$status" > "$out/immediate-original-gate.exit"
[[ $status == 0 ]] || exit "$status"
[[ $(cat "$build/post-failure-engine-reuse.exit") == 0 ]] || exit 2
cp "$build/norm-halving-arithmetic-census.bin" "$out/actual-census-executable.bin"
cp "$build/analyze.bin" "$out/actual-unchanged-full-analyzer.bin"
cargo metadata --offline --format-version 1 --manifest-path "$math/Cargo.toml" > "$out/math-metadata.json" 2> "$out/math-metadata.stderr.txt"
status=$?
printf '%s\n' "$status" > "$out/math-metadata.exit"
[[ $status == 0 ]] || exit "$status"
awk 'BEGIN { RS="\n\\[\\[package\\]\\]\n" } /source = / { print }' "$layout/original-layout/cryptanalysis/$study/norm-halving-evaluator/Cargo.lock" > "$out/original-registry-blocks.txt"
awk 'BEGIN { RS="\n\\[\\[package\\]\\]\n" } /source = / { print }' "$math/Cargo.lock" > "$out/derived-registry-blocks.txt"
cmp "$out/original-registry-blocks.txt" "$out/derived-registry-blocks.txt" > "$out/registry-compare.txt" 2>&1
status=$?
printf '%s\n' "$status" > "$out/registry-compare.exit"
[[ $status == 0 ]] || exit "$status"
timeout 120 cargo test --release --offline --locked --manifest-path "$math/Cargo.toml" --lib --no-run --message-format=json > "$out/math-compile.jsonl" 2> "$out/math-compile.stderr.txt"
status=$?
printf '%s\n' "$status" > "$out/math-compile.exit"
[[ $status == 0 ]] || exit "$status"
python3 - "$out" "$build" <<'PY'
from pathlib import Path
import hashlib,json,shutil,sys
o,b=map(Path,sys.argv[1:]);rows=[json.loads(x) for x in(o/'math-compile.jsonl').read_text().splitlines()];tests=[x for x in rows if x.get('reason')=='compiler-artifact' and x.get('executable')];assert len(tests)==1
x=tests[0];p=Path(x['executable']);q=o/'actual-math-test-executable.bin';shutil.copyfile(p,q);(o/'math-runtime-path.txt').write_text(str(p)+'\n');(o/'actual-math-executable.json').write_text(json.dumps(dict(Cargo_artifact=x,actual_copy=str(q),bytes=q.stat().st_size,sha256=hashlib.sha256(q.read_bytes()).hexdigest()),indent=2)+'\n')
engine=[x for x in rows if x.get('reason')=='compiler-artifact' and x.get('target',{}).get('name')=='isogeny_algos'];assert len(engine)==1 and engine[0]['fresh'] is True
before=json.loads((b/'engine-prepared.json').read_text());prior={Path(x['actual_path']).suffix:Path(x['copy']) for x in before['files']}
for key in ['package_id','manifest_path','target','profile','features','executable']:assert engine[0][key]==before['Cargo_artifact'][key],key
for filename in engine[0]['filenames']:assert Path(filename).read_bytes()==prior[Path(filename).suffix].read_bytes()
(o/'math-engine-reuse.json').write_text(json.dumps(dict(Cargo_artifact=engine[0],complete_prepared_library_bytes_equal=True),indent=2)+'\n')
PY
status=$?
printf '%s\n' "$status" > "$out/math-runtime-custody.exit"
[[ $status == 0 ]] || exit "$status"
exe=$(cat "$out/math-runtime-path.txt")
(ulimit -v 2097152; exec timeout 900 env N4_ARITHMETIC_OBSERVER=disabled "$exe" --nocapture --test-threads=1) > "$out/math-native.txt" 2>&1
status=$?
printf '%s\n' "$status" > "$out/math-native.exit"
[[ $status == 0 ]] || exit "$status"
grep -Eq '^test result: ok\. 4 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out;' "$out/math-native.txt" || exit 1
/workspace/scratch/ct74-norm-halving-audit-02/audit_native.bin --compare /workspace/scratch/ct74-norm-halving-audit-02/expected-native-05.json "$out/math-native.txt" "$out/all-four-whole-records.json" > "$out/math-whole-compare.txt" 2>&1
status=$?
printf '%s\n' "$status" > "$out/math-whole-compare.exit"
[[ $status == 0 ]] || exit "$status"
(ulimit -v 2097152; exec timeout 120 env N4_ARITHMETIC_OBSERVER=enabled "$out/actual-census-executable.bin" --controls) > "$out/primitive-native.txt" 2>&1
status=$?
printf '%s\n' "$status" > "$out/primitive-native.exit"
[[ $status == 0 ]] || exit "$status"
(ulimit -v 2097152; exec timeout 120 env N4_ARITHMETIC_OBSERVER=disabled "$out/actual-census-executable.bin" --case /intentionally-absent-fixture baseline 0) > "$out/disabled-native.txt" 2>&1
status=$?
printf '%s\n' "$status" > "$out/disabled-native.exit"
[[ $status == 2 ]] || exit 1
grep -F 'measurement and primitive controls require enabled observation' "$out/disabled-native.txt" >/dev/null || exit 1
mkdir "$out/cargo-bin"
cp /workspace/scratch/ct80_cargo_custody_wrapper.py "$out/cargo-bin/cargo"
chmod +x "$out/cargo-bin/cargo"
export CT80_CARGO_CUSTODY=$out/actual-canary-compiler-custody
export PATH="$out/cargo-bin:$PATH"
export N4_ARITHMETIC_OBSERVER=enabled
bash /workspace/cryptanalysis/$study/arithmetic-audit/canary.sh "$layout" "$out/actual-FpR-omission" > "$out/FpR-omission-caller.txt" 2>&1
status=$?
printf '%s\n' "$status" > "$out/FpR-omission-caller.exit"
[[ $status == 0 ]] || exit "$status"
bash "$source/quadratic-canary.sh" "$layout" "$out/actual-quadratic-omission" > "$out/quadratic-omission-caller.txt" 2>&1
status=$?
printf '%s\n' "$status" > "$out/quadratic-omission-caller.exit"
[[ $status == 0 ]] || exit "$status"
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
[[ $panel == 0 && $analysis == 0 && $parity == 0 ]] || exit 1
exit 0
