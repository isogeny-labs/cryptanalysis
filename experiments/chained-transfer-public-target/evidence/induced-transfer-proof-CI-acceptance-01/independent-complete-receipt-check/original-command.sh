#!/usr/bin/env bash
# Additive proof-only replay using both unchanged original repository gates.
set -euo pipefail
[[ $# == 2 ]] || exit 2
ci=$(cd -- "$(dirname -- "$0")" && pwd -P)
repo=$(git -C "$ci" rev-parse --show-toplevel)
producer=$(cd -- "$1" && pwd -P)
out=$(realpath -m "$2")
[[ ! -e $out ]] || exit 2
[[ $(realpath -m "$repo/../crypto") == "$producer" ]] || exit 2
case "$out/" in "$repo/"*|"$producer/"*) exit 2;; esac
study=experiments/chained-transfer-public-target
[[ $(git -C "$producer" rev-parse HEAD) == "$(cat "$repo/$study/upstream-commit.txt")" ]] || exit 2
mkdir "$out"
cd "$repo"
cp "$ci/check-01.sh" "$out/original-command.sh"
cp "$ci/reference-01.sha256" "$out/original-reference.sha256"
phase(){
 local name=$1;shift
 set +e
 "$@" 2>&1 | tee "$out/$name.txt"
 local codes=("${PIPESTATUS[@]}")
 set -e
 printf '%s %s\n' "${codes[0]}" "${codes[1]}" > "$out/$name.pipe-exits"
 printf '%s %s\n' "$name" "${codes[0]}" >> "$out/phases.txt"
 [[ ${codes[0]} == 0 && ${codes[1]} == 0 ]]
}
finish(){
 local status=$?;trap - EXIT;set +e
 sha256sum --check "$ci/reference-01.sha256" > "$out/final-source-guards.txt" 2>&1
 local guard=$?
 cmp "$ci/reference-01.sha256" "$out/original-reference.sha256" >> "$out/final-source-guards.txt" 2>&1 || guard=1
 printf '%s\n' "$guard" > "$out/final-source-guards.exit"
 [[ $status -ne 0 || $guard -eq 0 ]] || status=$guard
 printf '%s\n' "$status" > "$out/original.exit"
 date -u +%FT%TZ > "$out/finish.txt"
 exit "$status"
}
trap finish EXIT
date -u +%FT%TZ > "$out/start.txt"
git rev-parse HEAD > "$out/consumer-head.txt"
git -C "$producer" rev-parse HEAD > "$out/producer-head.txt"
phase initial-source-guards sha256sum --check "$ci/reference-01.sha256"
phase consumer-toolchain env ELAN_TOOLCHAIN=leanprover/lean4:v4.34.1 lean --version
phase producer-toolchain env ELAN_TOOLCHAIN=leanprover/lean4:v4.35.0 lean --version
source_file=$study/original-induced-transfer-01/lean/InducedFullTransfer.lean
cp "$repo/$source_file" "$out/actual-consumer-InducedFullTransfer.lean"
mkdir -p "$producer/target"
stage=$(mktemp -d "$producer/target/induced-full-transfer-proof.XXXXXX")
cp "$repo/$source_file" "$stage/InducedFullTransfer.lean"
cp "$stage/InducedFullTransfer.lean" "$out/actual-producer-InducedFullTransfer.lean"
phase consumer-proof timeout 120 env ELAN_TOOLCHAIN=leanprover/lean4:v4.34.1 bash tools/lean/proof-gate.sh --out "$out/consumer-proofs" "$source_file"
phase producer-proof timeout 120 bash -c 'cd "$1"; shift; exec env ELAN_TOOLCHAIN=leanprover/lean4:v4.35.0 bash tools/lean/proof-gate.sh "$@"' _ "$producer" --out "$out/producer-proofs" "${stage#"$producer/"}/InducedFullTransfer.lean"
while IFS= read -r claim; do
 phase "binding-$claim" timeout 120 env ELAN_TOOLCHAIN=leanprover/lean4:v4.34.1 python3 tools/pcc/pcc.py verify "pcc/claims/$claim.json" --json
done < "$ci/statement-bindings-01.txt"
phase exact-coverage python3 "$ci/validate_receipts_01.py" "$repo" "$out"
phase final-source-guards sha256sum --check "$ci/reference-01.sha256"
echo 'Both original gates audit all21 declarations, including nine named mathematical roots and12 structural declarations; allnine exact bindings. Unsigned proof replay only.'
