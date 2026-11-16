#!/usr/bin/env bash
set -u
[[ $# == 2 ]] || exit 2
expected=$1
out=$(realpath -m "$2")
pkg=$(cd -- "$(dirname -- "$0")" && pwd -P)
build=/workspace/scratch/ct80-twisted-pair-build-02
[[ ! -e $out && $(git rev-parse HEAD) == "$expected" && -z $(git status --porcelain) ]] || exit 2
mkdir "$out"
trap 'status=$?; printf "%s\n" "$status" > "$out/orchestrator.exit"; date -u +%FT%TZ > "$out/finish.txt"' EXIT
cp "$0" "$out/original-command.sh"
date -u +%FT%TZ > "$out/start.txt"
bash scripts/checkpoint.sh gate > "$out/immediate-original-gate.txt" 2>&1
status=$?
printf '%s\n' "$status" > "$out/immediate-original-gate.exit"
[[ $status == 0 ]] || exit "$status"
python3 - "$pkg" "$build" "$out" <<'PY'
from pathlib import Path
import hashlib,json,shutil,sys
pkg,build,out=map(Path,sys.argv[1:]);assert(build/'orchestrator.exit').read_text().strip()=='0'
for p in sorted((build/'actual-source').rglob('*')):
 if p.is_file():assert p.read_bytes()==(pkg/p.relative_to(build/'actual-source')).read_bytes(),str(p)
for label in ['test','auditor']:
 record=json.loads((build/('actual-'+label+'-executable.json')).read_text());p=Path(record['Cargo_artifact']['executable']);copy=Path(record['actual_copy']);assert p.read_bytes()==copy.read_bytes() and hashlib.sha256(p.read_bytes()).hexdigest()==record['sha256']
 shutil.copy2(p,out/('actual-'+label+'-executable.bin'));(out/(label+'-runtime-path.txt')).write_text(str(p)+'\n');(out/(label+'-runtime-custody.json')).write_text(json.dumps(dict(**record,full_compiler_runtime_bytes_equal=True,whole_compiled_source_equal=True),indent=2)+'\n')
PY
status=$?
printf '%s\n' "$status" > "$out/runtime-custody.exit"
[[ $status == 0 ]] || exit "$status"
sha256sum --check "$pkg/frozen-prior-inputs-01.sha256" > "$out/prior981.txt" 2>&1
status=$?
printf '%s\n' "$status" > "$out/prior981.exit"
[[ $status == 0 ]] || exit "$status"
exe=$(cat "$out/test-runtime-path.txt")
(ulimit -v 2097152; exec timeout 900 "$exe" --nocapture --test-threads=1) > "$out/native.txt" 2>&1
status=$?
printf '%s\n' "$status" > "$out/native.exit"
[[ $status == 0 ]] || exit "$status"
auditor=$(cat "$out/auditor-runtime-path.txt")
timeout 120 "$auditor" --freeze "$out/native.txt" "$out/expected-whole-native-01.json" > "$out/freeze.txt" 2>&1
status=$?
printf '%s\n' "$status" > "$out/freeze.exit"
[[ $status == 0 ]] || exit "$status"
timeout 120 "$auditor" --compare "$out/expected-whole-native-01.json" "$out/native.txt" "$out/all-nine-whole-records.json" > "$out/whole-compare.txt" 2>&1
status=$?
printf '%s\n' "$status" > "$out/whole-compare.exit"
[[ $status == 0 ]] || exit "$status"
sed '/N4_TWIST_MATCHED_PAIR /d' "$out/native.txt" > "$out/actual-whole-matched-pair-omitted.txt"
timeout 120 "$auditor" --compare "$out/expected-whole-native-01.json" "$out/actual-whole-matched-pair-omitted.txt" "$out/must-not-accept-omission.json" > "$out/omission.txt" 2>&1
status=$?
printf '%s\n' "$status" > "$out/omission.exit"
[[ $status == 101 && ! -e $out/must-not-accept-omission.json ]] || exit 1
sha256sum --check "$pkg/frozen-prior-inputs-01.sha256" > "$out/final-prior981.txt" 2>&1
status=$?
printf '%s\n' "$status" > "$out/final-prior981.exit"
exit "$status"
