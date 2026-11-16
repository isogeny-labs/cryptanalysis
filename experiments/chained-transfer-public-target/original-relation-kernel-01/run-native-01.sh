#!/usr/bin/env bash
# Whole passive capture only; rank/norm/BSGS interpretation is a later phase.
set -u
[[ $# == 3 ]] || exit 2
expected=$1
out=$(realpath -m "$2")
build=$(realpath -m "$3")
pkg=$(cd -- "$(dirname -- "$0")" && pwd -P)
repo=$(git -C "$pkg" rev-parse --show-toplevel)
cd "$repo" || exit 2
[[ ! -e $out && $(git rev-parse HEAD) == "$expected" && -z $(git status --porcelain) ]] || exit 2
mkdir "$out"
trap 'status=$?;printf "%s\n" "$status" > "$out/original.exit";date -u +%FT%TZ > "$out/finish.txt"' EXIT
date -u +%FT%TZ > "$out/start.txt"
cp "$pkg/run-native-01.sh" "$out/original-command.sh"
cp "$pkg/frozen-native-driver-01.sha256" "$out/original-native-driver.sha256"
phase(){ local name=$1 want=$2;shift 2;"$@" > "$out/$name.txt" 2>&1;local status=$?;printf '%s\n' "$status" > "$out/$name.exit";printf '%s %s %s\n' "$name" "$want" "$status" >> "$out/phases.txt";[[ $status == "$want" ]]; }
phase immediate-original-gate 0 bash scripts/checkpoint.sh gate || exit 1
phase runtime-custody 0 python3 "$pkg/runtime_custody.py" "$pkg" "$build" "$out" || exit 1
phase initial-prior 0 sha256sum --check "$pkg/frozen-prior-inputs-01.sha256" || exit 1
phase initial-current 0 sha256sum --check "$pkg/frozen-current-inputs-01.sha256" || exit 1
phase initial-native-driver 0 sha256sum --check "$pkg/frozen-native-driver-01.sha256" || exit 1
test=$(cat "$out/chain-actual-path.txt")
auditor=$(cat "$out/auditor-actual-path.txt")
native_auditor=$(cat "$out/native-auditor-actual-path.txt")
export N4_RELATION_TRACE_OUTPUT=$out/whole60-passive-trace.json
phase native 0 bash -c 'ulimit -v 2097152;exec timeout 900 "$1" --nocapture --test-threads=1' _ "$test" || exit 1
grep -Eq '^test result: ok\. 1 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out;' "$out/native.txt" || exit 1
phase freeze-whole-native 0 timeout 120 "$native_auditor" --freeze "$out/native.txt" "$out/whole100-same-run-frozen.json" || exit 1
phase compare-whole-native 0 timeout 120 "$native_auditor" --compare "$out/whole100-same-run-frozen.json" "$out/native.txt" "$out/whole100-same-run-compared.json" || exit 1
phase whole60-capture-and-report-parity 0 bash -c 'ulimit -v 2097152;exec timeout 900 "$1" --audit "$2" "$3" "$4" "$5" "$6"' _ "$auditor" "$out/original-IC-whole100-baseline.json" "$out/native.txt" "$N4_RELATION_TRACE_OUTPUT" "$out/whole60-passive-trace.journal.jsonl" "$out/whole60-accepted-capture.json" || exit 1
for stage in available selected candidate descent; do
 omitted=$out/$stage-entire-capture-stage-omitted.json.xz
 phase "$stage-materialize-whole-XZ" 0 python3 "$pkg/omit_capture_stage.py" "$N4_RELATION_TRACE_OUTPUT" "$stage" "$omitted" || exit 1
 phase "$stage-whole-XZ-CRC" 0 xz --test "$omitted" || exit 1
 phase "$stage-omission" 101 bash -c 'exec timeout 120 "$1" --audit "$2" "$3" <(xz -dc "$4") "$5" "$6"' _ "$auditor" "$out/original-IC-whole100-baseline.json" "$out/native.txt" "$omitted" "$out/whole60-passive-trace.journal.jsonl" "$out/$stage-must-not-accept.json" || exit 1
 [[ ! -e $out/$stage-must-not-accept.json ]] || exit 1
done
for label in chain auditor native-auditor; do
 actual=$(cat "$out/$label-actual-path.txt")
 phase "final-$label-bytes" 0 cmp "$actual" "$out/actual-before-native-$label.bin" || exit 1
done
phase final-prior 0 sha256sum --check "$pkg/frozen-prior-inputs-01.sha256" || exit 1
phase final-current 0 sha256sum --check "$pkg/frozen-current-inputs-01.sha256" || exit 1
phase final-native-driver 0 sha256sum --check "$pkg/frozen-native-driver-01.sha256" || exit 1
phase final-native-driver-copy 0 cmp "$pkg/frozen-native-driver-01.sha256" "$out/original-native-driver.sha256" || exit 1
exit 0
