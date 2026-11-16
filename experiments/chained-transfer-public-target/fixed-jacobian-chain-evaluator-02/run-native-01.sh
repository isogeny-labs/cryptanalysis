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
trap 'status=$?; printf "%s\n" "$status" > "$out/original.exit"; date -u +%FT%TZ > "$out/finish.txt"' EXIT
date -u +%FT%TZ > "$out/start.txt"
cp "$pkg/run-native-01.sh" "$out/original-command.sh"
phase(){ local name=$1 want=$2;shift 2;"$@" > "$out/$name.txt" 2>&1;local status=$?;printf '%s\n' "$status" > "$out/$name.exit";printf '%s %s %s\n' "$name" "$want" "$status" >> "$out/phases.txt";[[ $status == "$want" ]]; }
phase immediate-original-gate 0 bash scripts/checkpoint.sh gate || exit 1
phase runtime-custody 0 python3 "$pkg/runtime_custody.py" "$pkg" "$build" "$out" || exit 1
phase initial-prior 0 sha256sum --check "$pkg/frozen-prior-inputs-01.sha256" || exit 1
test=$(cat "$out/chain-actual-path.txt")
auditor=$(cat "$out/auditor-actual-path.txt")
deriver=$(cat "$out/deriver-actual-path.txt")
phase derive695 0 timeout 120 "$deriver" "$out/baseline695.json" "$out/all695-expected.json" || exit 1
phase native 0 bash -c 'ulimit -v 2097152; exec timeout 900 "$1" --nocapture --test-threads=1' _ "$test" || exit 1
phase compare695 0 timeout 120 "$auditor" --compare "$out/old-sixteen.json" "$out/all695-expected.json" "$out/native.txt" "$out/all695-compared.json" || exit 1
for tag in N4_FIXED_CHAIN_EXCEPTIONAL_CASE N4_FIXED_CHAIN_ALL_EXCEPTIONALS N4_FIXED_CHAIN_ALL_PUBLIC N4_FIXED_CHAIN_SELECTED_CALL_VECTORS; do
 sed "/$tag /d" "$out/native.txt" > "$out/$tag-entire-actual-records-omitted.txt"
 phase "$tag-omission" 101 timeout 120 "$auditor" --compare "$out/old-sixteen.json" "$out/all695-expected.json" "$out/$tag-entire-actual-records-omitted.txt" "$out/$tag-must-not-accept.json" || exit 1
 [[ ! -e $out/$tag-must-not-accept.json ]] || exit 1
done
phase final-test-bytes 0 cmp "$test" "$out/actual-before-native-chain.bin" || exit 1
phase final-auditor-bytes 0 cmp "$auditor" "$out/actual-before-native-auditor.bin" || exit 1
phase final-deriver-bytes 0 cmp "$deriver" "$out/actual-before-native-deriver.bin" || exit 1
phase final-prior 0 sha256sum --check "$pkg/frozen-prior-inputs-01.sha256" || exit 1
exit 0
