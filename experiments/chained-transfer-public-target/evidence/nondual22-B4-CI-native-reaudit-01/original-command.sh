#!/usr/bin/env bash
set -u
[[ $# == 2 ]] || exit 2
head=$1
out=$(realpath -m "$2")
source=/workspace/scratch/ct80-B4-new22-CI-acceptance-01/members
[[ ! -e $out && $(git rev-parse HEAD) == "$head" && -z $(git status --porcelain) ]] || exit 2
mkdir "$out"
trap 'status=$?; printf "%s\n" "$status" > "$out/orchestrator.exit"' EXIT
cp "$0" "$out/original-command.sh"
bash scripts/checkpoint.sh gate > "$out/immediate-original-gate.txt" 2>&1
status=$?
printf '%s\n' "$status" > "$out/immediate-original-gate.exit"
[[ $status == 0 ]] || exit "$status"
for name in audit_native audit_models audit_records; do
 install -m755 "$source/$name.actual-executable.bin" "$out/$name.bin"
 cmp "$source/$name.actual-executable.bin" "$out/$name.bin" || exit 1
done
function phase {
 label=$1
 expected=$2
 shift 2
 timeout 120 "$@" > "$out/$label.txt" 2>&1
 actual=$?
 printf '%s %s %s\n' "$label" "$actual" "$expected" >> "$out/phases.txt"
 [[ $actual == "$expected" ]] || exit 1
}
phase second-edge 0 "$out/audit_native.bin" --compare "$source/second-edge-expected.json" "$source/second-edge-native.txt" "$out/second-edge-all.json"
phase second-model 0 "$out/audit_models.bin" --compare "$source/second-model-expected.json" "$source/second-model-native.txt" "$out/second-model-all.json"
phase third-edge 0 "$out/audit_records.bin" --compare edge "$source/third-edge-expected.json" "$source/third-edge-native.txt" "$out/third-edge-all.json"
phase third-model 0 "$out/audit_records.bin" --compare model "$source/third-model-expected.json" "$source/third-model-native.txt" "$out/third-model-all.json"
phase omit-second-edge 101 "$out/audit_native.bin" --compare "$source/second-edge-expected.json" "$source/second-edge-whole-record-omitted.txt" "$out/invalid-second-edge.json"
phase omit-second-model 101 "$out/audit_models.bin" --compare "$source/second-model-expected.json" "$source/second-model-whole-record-omitted.txt" "$out/invalid-second-model.json"
phase omit-third-edge 101 "$out/audit_records.bin" --compare edge "$source/third-edge-expected.json" "$source/third-edge-whole-record-omitted.txt" "$out/invalid-third-edge.json"
phase omit-third-model 101 "$out/audit_records.bin" --compare model "$source/third-model-expected.json" "$source/third-model-whole-record-omitted.txt" "$out/invalid-third-model.json"
phase first-backtrack 0 "$out/audit_records.bin" --old-control "$source/first-backtrack.txt" "$out/first-backtrack-all.json"
phase second-backtrack 0 "$out/audit_records.bin" --control "$source/second-backtrack.txt" "$out/second-backtrack-all.json"
[[ ! -e $out/invalid-second-edge.json && ! -e $out/invalid-second-model.json && ! -e $out/invalid-third-edge.json && ! -e $out/invalid-third-model.json ]] || exit 1
