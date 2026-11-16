#!/usr/bin/env bash
# Thin execution of the published whole-input contract, not a fresh solver replay.
set -euo pipefail
[[ $# == 4 ]] || exit 2
expected=$1
out=$(realpath -m "$2")
build=$(realpath -m "$3")
ram=$(realpath -m "$4")
pkg=$(cd -- "$(dirname -- "$0")" && pwd -P)
repo=$(git -C "$pkg" rev-parse --show-toplevel)
cd "$repo"
[[ $(git rev-parse HEAD) == "$expected" && -z $(git status --porcelain) && ! -e $out && ! -e $ram ]] || exit 2
mkdir "$out"
trap 'status=$?;printf "%s\n" "$status" > "$out/original.exit";date -u +%FT%TZ > "$out/finish.txt"' EXIT
date -u +%FT%TZ > "$out/start.txt"
cp "$0" "$out/original-command.sh"
phase(){
 local name=$1 want=$2;shift 2
 set +e
 "$@" > "$out/$name.txt" 2>&1
 local code=$?
 set -e
 printf '%s\n' "$code" > "$out/$name.exit"
 printf '%s %s %s\n' "$name" "$want" "$code" >> "$out/phases.txt"
 printf '%s %s\n' "$name" "$code"
 [[ $code == "$want" ]]
}
bounded(){ (ulimit -v 2097152;exec timeout 120 "$@"); }
phase immediate-original-checkpoint-gate 0 bash scripts/checkpoint.sh gate
phase original1532guards 0 sha256sum --check experiments/chained-transfer-public-target/original-relation-character-01/frozen-prior-inputs-01.sha256
phase current-source-guards 0 sha256sum --check "$pkg/frozen-comparator-inputs-01.sha256"
for name in Cargo.toml Cargo.lock src/lib.rs src/main.rs; do
 phase "literal-build-${name//\//-}" 0 cmp "$pkg/audit/$name" "$build/actual-source/$name"
done
binary=/dev/shm/ct107-whole-relation-comparator-target/release/audit-original-relation-historical
phase exact-compiled-runtime-bytes 0 cmp "$binary" "$build/actual-compiled-auditor.bin"
cp "$binary" "$out/actual-before-runtime-auditor.bin"
sha256sum "$binary" "$out/actual-before-runtime-auditor.bin" > "$out/runtime-whole-binary-sha256.txt"
pins=$pkg/historical-whole-fixture-pins-01.json
docs=$repo/docs/research-artifacts/chained-transfer/original-relation-rank-character-27
capture=$pkg/historical-passive-acceptance-01.json
mkdir "$ram"
phase whole-historical-byte-materialization 0 bounded "$binary" --fixture-bundle "$pins" "$docs" "$capture" "$ram/positive"
phase whole-historical-positive-comparison 0 bounded "$binary" --compare "$pins" "$docs" "$capture" "$ram/positive" "$out/whole-positive-accepted.json"
phase materialize-entire-control-bundles 0 bounded "$binary" --controls "$ram/positive" "$ram/controls"
for control in timing-only missing-record-class changed-counter changed-relation changed-kernel missing-rank-call changed-character-scalar unexpected-verdict-field unbound-linked-hash; do
 want=1
 [[ $control != timing-only ]] || want=0
 accepted=$out/$control-accepted.json
 phase "whole-$control" "$want" bounded "$binary" --compare "$pins" "$docs" "$capture" "$ram/controls/$control" "$accepted"
 if [[ $want == 1 ]]; then [[ ! -e $accepted ]] || exit 1;else [[ -f $accepted ]] || exit 1;fi
done
phase whole-positive-and-all-controls-archive 0 timeout 120 bash -o pipefail -c 'tar -cf - -C "$1" . | xz -T1 -1 > "$2";codes=("${PIPESTATUS[@]}");printf "%s\n" "${codes[*]}";[[ ${codes[0]} == 0 && ${codes[1]} == 0 ]]' _ "$ram" "$out/entire-positive-and-controls.tar.xz"
phase whole-control-archive-CRC 0 timeout 120 xz --test "$out/entire-positive-and-controls.tar.xz"
phase whole-control-archive-all-original-bytes 0 timeout 120 bash -o pipefail -c 'xz -dc "$1" | tar -df - -C "$2";codes=("${PIPESTATUS[@]}");printf "%s\n" "${codes[*]}";[[ ${codes[0]} == 0 && ${codes[1]} == 0 ]]' _ "$out/entire-positive-and-controls.tar.xz" "$ram"
phase final-exact-runtime-bytes 0 cmp "$binary" "$out/actual-before-runtime-auditor.bin"
phase final-current-source-guards 0 sha256sum --check "$pkg/frozen-comparator-inputs-01.sha256"
phase final-original1532guards 0 sha256sum --check experiments/chained-transfer-public-target/original-relation-character-01/frozen-prior-inputs-01.sha256
