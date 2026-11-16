#!/usr/bin/env bash
set -u
[[ $# == 4 ]] || exit 2
expected=$1
out=$(realpath -m "$2")
build=$(realpath -m "$3")
bins=$(realpath -m "$4")
pkg=$(cd -- "$(dirname -- "$0")" && pwd -P)
repo=$(git -C "$pkg" rev-parse --show-toplevel)
cd "$repo" || exit 2
[[ ! -e $out && $(git rev-parse HEAD) == "$expected" && -z $(git status --porcelain) ]] || exit 2
mkdir "$out"
trap 'status=$?; printf "%s\n" "$status" > "$out/original.exit"; date -u +%FT%TZ > "$out/finish.txt"' EXIT
cp "$0" "$out/original-command.sh"
date -u +%FT%TZ > "$out/start.txt"
phase(){
 local name=$1 want=$2;shift 2
 "$@" > "$out/$name.txt" 2>&1
 local status=$?
 printf '%s\n' "$status" > "$out/$name.exit"
 printf '%s %s %s\n' "$name" "$want" "$status" >> "$out/phases.txt"
 [[ $status == "$want" ]]
}
phase immediate-original-gate 0 bash scripts/checkpoint.sh gate || exit 1
phase runtime-custody 0 python3 "$pkg/runtime_custody.py" "$pkg" "$build" "$bins" "$out" || exit 1
phase prior1028 0 sha256sum --check "$pkg/frozen-prior-inputs-01.sha256" || exit 1
xz -dc "$pkg/../twisted-pair-preflight/expected-native-02.json.xz" > "$out/old-nine.json" || exit 1
test=$(cat "$out/test-actual-path.txt")
auditor=$(cat "$out/auditor-actual-path.txt")
control=$(cat "$out/control-actual-path.txt")
phase native 0 bash -c 'ulimit -v 2097152; exec timeout 900 "$1" --nocapture --test-threads=1' _ "$test" || exit 1
phase freeze16 0 timeout 120 "$auditor" --freeze "$out/old-nine.json" "$out/native.txt" "$out/all-sixteen-expected.json" || exit 1
phase compare16 0 timeout 120 "$auditor" --compare "$out/old-nine.json" "$out/all-sixteen-expected.json" "$out/native.txt" "$out/all-sixteen-compared.json" || exit 1
for tag in N4_FOURTH_PUBLIC N4_FOURTH_MATCHED_ENDPOINTS; do
 sed "/$tag /d" "$out/native.txt" > "$out/$tag-entire-actual-record-omitted.txt"
 phase "$tag-omission" 101 timeout 120 "$auditor" --compare "$out/old-nine.json" "$out/all-sixteen-expected.json" "$out/$tag-entire-actual-record-omitted.txt" "$out/$tag-must-not-accept.json" || exit 1
 [[ ! -e $out/$tag-must-not-accept.json ]] || exit 1
done
phase actual-old-third-dual 101 bash -c 'ulimit -v 2097152; exec timeout 900 "$1"' _ "$control" || exit 1
phase old-third-dual-whole-data 0 timeout 120 "$auditor" --control "$out/old-nine.json" "$out/actual-old-third-dual.txt" "$out/all-five-old-dual-control-records.json" || exit 1
phase final-prior1028 0 sha256sum --check "$pkg/frozen-prior-inputs-01.sha256" || exit 1
exit 0
