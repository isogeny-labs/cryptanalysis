#!/usr/bin/env bash
set -u
out=/workspace/scratch/ct80-observer-unit-native-03
build=/workspace/scratch/ct79-observer-unit-build-03
[[ ! -e $out && $(git rev-parse HEAD) == b4e3543018ddc5ed70a34ee17280f23b8848484c && -z $(git status --porcelain) ]] || exit 2
mkdir "$out"
cp "$0" "$out/original-command.sh"
bash scripts/checkpoint.sh gate > "$out/immediate-original-gate.txt" 2>&1
status=$?
printf '%s\n' "$status" > "$out/immediate-original-gate.exit"
[[ $status == 0 ]] || exit "$status"
python3 - "$out" "$build" <<'PY'
from pathlib import Path
import hashlib,json,shutil,sys
o,b=map(Path,sys.argv[1:]);record=json.loads((b/'actual-binary.json').read_text());p=Path(record['Cargo_artifact']['executable']);copy=b/'actual-test-executable.bin'
assert p.read_bytes()==copy.read_bytes() and hashlib.sha256(copy.read_bytes()).hexdigest()==record['sha256']
source=Path('/workspace/cryptanalysis/experiments/chained-transfer-public-target/norm-arithmetic-storage-02/taps')
for f in sorted((b/'actual-source').rglob('*')):
 if f.is_file():assert f.read_bytes()==(source/f.relative_to(b/'actual-source')).read_bytes(),str(f)
shutil.copyfile(p,o/'actual-runtime-executable.bin');(o/'runtime-custody.json').write_text(json.dumps(dict(**record,full_compiler_runtime_bytes_equal=True,whole_compiled_source_equal=True),indent=2)+'\n')
PY
status=$?
printf '%s\n' "$status" > "$out/runtime-custody.exit"
[[ $status == 0 ]] || exit "$status"
exe=$(python3 - "$build/actual-binary.json" <<'PY'
import json,sys
print(json.load(open(sys.argv[1]))['Cargo_artifact']['executable'])
PY
)
(ulimit -v 2097152; exec timeout 120 env N4_ARITHMETIC_OBSERVER=enabled "$exe" --nocapture --test-threads=1) > "$out/native.txt" 2>&1
status=$?
printf '%s\n' "$status" > "$out/native.exit"
[[ $status == 0 ]] || exit "$status"
grep -Eq '^test result: ok\. 1 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out;' "$out/native.txt" || exit 1
sha256sum --check experiments/chained-transfer-public-target/observer-storage-prior-inputs-02.sha256 > "$out/final-prior24.txt"
status=$?
printf '%s\n' "$status" > "$out/final-prior24.exit"
exit "$status"
