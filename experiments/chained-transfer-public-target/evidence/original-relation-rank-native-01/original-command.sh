#!/usr/bin/env bash
set -u
[[ $# == 4 ]] || exit 2
expected=$1
out=$(realpath -m "$2")
build=$(realpath -m "$3")
ram=$(realpath -m "$4")
pkg=$(cd -- "$(dirname -- "$0")" && pwd -P)
repo=$(git -C "$pkg" rev-parse --show-toplevel)
cd "$repo" || exit 2
[[ ! -e $out && ! -e $ram && $(git rev-parse HEAD) == "$expected" && -z $(git status --porcelain) ]] || exit 2
mkdir "$out" "$ram"
trap 'status=$?;printf "%s\n" "$status" > "$out/original.exit";date -u +%FT%TZ > "$out/finish.txt"' EXIT
date -u +%FT%TZ > "$out/start.txt"
cp "$pkg/run-native-01.sh" "$out/original-command.sh"
phase(){ local name=$1 want=$2;shift 2;"$@" > "$out/$name.txt" 2>&1;local status=$?;printf '%s\n' "$status" > "$out/$name.exit";printf '%s %s %s\n' "$name" "$want" "$status" >> "$out/phases.txt";[[ $status == "$want" ]]; }
phase immediate-original-gate 0 bash scripts/checkpoint.sh gate || exit 1
phase initial-source 0 sha256sum --check "$pkg/frozen-current-inputs-01.sha256" || exit 1
phase runtime-custody 0 python3 "$pkg/runtime_custody.py" "$pkg" "$build" "$out" || exit 1
producer=$(cat "$out/producer-actual-path.txt")
replay=$(cat "$out/replay-actual-path.txt")
controls=$(cat "$out/controls-actual-path.txt")
trace=/workspace/scratch/ct101-original-relation-kernel-native-01/whole60-passive-trace.json
gate=/workspace/scratch/ct101-original-relation-kernel-native-01/whole60-accepted-capture.json
cert=$ram/whole60-certificates.jsonl
phase produce-all360-certificates 0 bash -c 'ulimit -v 2097152;exec timeout 900 "$@"' _ "$producer" "$trace" "$gate" "$cert" || exit 1
phase independent-all360-replay 0 bash -c 'ulimit -v 2097152;exec timeout 900 "$@"' _ "$replay" "$trace" "$gate" "$cert" "$out/whole60-independent-verdict.json" || exit 1
phase materialize-whole-mathematical-controls 0 bash -c 'ulimit -v 2097152;exec timeout 120 "$@"' _ "$controls" "$cert" "$ram/whole-matrix-coefficient-modified.jsonl" "$ram/whole-constrained-kernel-modified.jsonl" || exit 1
for name in matrix-coefficient constrained-kernel; do
 phase "$name-modified-rejection" 101 bash -c 'ulimit -v 2097152;exec timeout 900 "$@"' _ "$replay" "$trace" "$gate" "$ram/whole-$name-modified.jsonl" "$out/$name-must-not-accept.json" || exit 1
 [[ ! -e $out/$name-must-not-accept.json ]] || exit 1
done
for name in whole60-certificates whole-matrix-coefficient-modified whole-constrained-kernel-modified; do
 phase "$name-whole-XZ" 0 bash -c 'exec xz -T1 -c "$1" > "$2"' _ "$ram/$name.jsonl" "$out/$name.jsonl.xz" || exit 1
 phase "$name-whole-XZ-CRC" 0 xz --test "$out/$name.jsonl.xz" || exit 1
 phase "$name-whole-decoded-byte-compare" 0 bash -o pipefail -c 'xz -dc "$1" | cmp - "$2"; code=("${PIPESTATUS[@]}");printf "%s\n" "${code[*]}";[[ ${code[0]} == 0 && ${code[1]} == 0 ]]' _ "$out/$name.jsonl.xz" "$ram/$name.jsonl" || exit 1
done
for label in producer replay controls; do
 actual=$(cat "$out/$label-actual-path.txt")
 phase "final-$label-bytes" 0 cmp "$actual" "$out/actual-before-$label.bin" || exit 1
done
phase final-source 0 sha256sum --check "$pkg/frozen-current-inputs-01.sha256" || exit 1
phase final-entire-trace-custody 0 python3 "$pkg/runtime_custody.py" "$pkg" "$build" "$out" || exit 1
exit 0
