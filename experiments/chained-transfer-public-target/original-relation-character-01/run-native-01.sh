#!/usr/bin/env bash
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
phase(){ local name=$1 want=$2;shift 2;"$@" > "$out/$name.txt" 2>&1;local status=$?;printf '%s\n' "$status" > "$out/$name.exit";printf '%s %s %s\n' "$name" "$want" "$status" >> "$out/phases.txt";[[ $status == "$want" ]]; }
phase immediate-original-gate 0 bash scripts/checkpoint.sh gate || exit 1
phase initial-prior 0 sha256sum --check "$pkg/frozen-prior-inputs-01.sha256" || exit 1
phase initial-compiled-source 0 sha256sum --check "$pkg/frozen-current-inputs-01.sha256" || exit 1
phase initial-native-driver 0 sha256sum --check "$pkg/frozen-native-driver-01.sha256" || exit 1
phase runtime-custody 0 python3 "$pkg/runtime_custody.py" "$pkg" "$build" "$out" || exit 1
producer=$(cat "$out/producer-actual-path.txt")
auditor=$(cat "$out/auditor-actual-path.txt")
control=$(cat "$out/control-actual-path.txt")
trace=/workspace/scratch/ct101-original-relation-kernel-native-01/whole60-passive-trace.json
rank=/workspace/scratch/ct102-original-relation-rank-native-01/whole60-independent-verdict.json
witnesses=$out/whole60-source-character-witnesses.jsonl
phase generate-whole60-witnesses 0 bash -c 'ulimit -v 2097152;exec timeout 900 "$@"' _ "$producer" "$trace" "$rank" "$witnesses" || exit 1
phase independent-whole60-direct-source-and-descent-audit 0 bash -c 'ulimit -v 2097152;exec timeout 900 "$@"' _ "$auditor" "$trace" "$rank" "$witnesses" "$out/whole60-source-character-verdict.json" || exit 1
phase whole-scalar-mutation 0 bash -c 'ulimit -v 2097152;exec timeout 120 "$@"' _ "$control" "$witnesses" "$out/whole60-scalar-witness-modified.jsonl" || exit 1
phase scalar-witness-modified-rejection 101 bash -c 'ulimit -v 2097152;exec timeout 900 "$@"' _ "$auditor" "$trace" "$rank" "$out/whole60-scalar-witness-modified.jsonl" "$out/scalar-must-not-accept.json" || exit 1
[[ ! -e $out/scalar-must-not-accept.json ]] || exit 1
for name in whole60-source-character-witnesses whole60-scalar-witness-modified; do
 phase "$name-whole-XZ" 0 bash -c 'exec xz -T1 -c "$1" > "$2"' _ "$out/$name.jsonl" "$out/$name.jsonl.xz" || exit 1
 phase "$name-whole-XZ-CRC" 0 xz --test "$out/$name.jsonl.xz" || exit 1
 phase "$name-whole-decoded-byte-compare" 0 bash -o pipefail -c 'xz -dc "$1" | cmp - "$2";code=("${PIPESTATUS[@]}");printf "%s\n" "${code[*]}";[[ ${code[0]} == 0 && ${code[1]} == 0 ]]' _ "$out/$name.jsonl.xz" "$out/$name.jsonl" || exit 1
done
for label in producer auditor control; do
 actual=$(cat "$out/$label-actual-path.txt")
 phase "final-$label-bytes" 0 cmp "$actual" "$out/actual-before-$label.bin" || exit 1
done
phase final-prior 0 sha256sum --check "$pkg/frozen-prior-inputs-01.sha256" || exit 1
phase final-compiled-source 0 sha256sum --check "$pkg/frozen-current-inputs-01.sha256" || exit 1
phase final-native-driver 0 sha256sum --check "$pkg/frozen-native-driver-01.sha256" || exit 1
phase final-entire-runtime-prepared-input-custody 0 python3 "$pkg/runtime_custody.py" "$pkg" "$build" "$out" || exit 1
exit 0
