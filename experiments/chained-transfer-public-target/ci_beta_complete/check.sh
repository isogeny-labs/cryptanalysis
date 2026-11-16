#!/usr/bin/env bash
# Thin orchestration. Rust/Lean perform the scientific checks.
set -euo pipefail
[[ $# == 2 ]] || exit 2
ci=$(cd -- "$(dirname -- "$0")" && pwd -P)
repo=$(git -C "$ci" rev-parse --show-toplevel)
producer=$(cd -- "$1" && pwd -P)
out=$(realpath -m "$2")
cache=${out}-build-cache
[[ ! -e $out && ! -e $cache ]] || exit 2
case "$out/" in "$repo/"*|"$producer/"*) exit 2;; esac
[[ $(realpath -m "$repo/../crypto") == "$producer" ]] || exit 2
for tool in cargo rustc lean lake python3 jq xz; do command -v "$tool" >/dev/null || exit 2; done
study=experiments/chained-transfer-public-target
[[ $(git -C "$producer" rev-parse HEAD) == "$(cat "$repo/$study/upstream-commit.txt")" ]] || exit 2
mkdir "$out"
export RUSTUP_TOOLCHAIN=1.99.1
export CARGO_TARGET_DIR=$cache
cd "$repo"
manifest=$repo/$study/beta-complete-evaluator/Cargo.toml
reference=$ci/reference-01.sha256
cp "$reference" "$out/original-reference.sha256"
phase() {
 local name=$1 expected=$2; shift 2
 set +e
 "$@" 2>&1 | tee "$out/$name.txt"
 local codes=("${PIPESTATUS[@]}")
 set -e
 printf '%s %s\n' "${codes[0]}" "${codes[1]}" > "$out/$name.pipe-exits"
 printf '%s %s %s\n' "$name" "$expected" "${codes[0]}" >> "$out/phases.txt"
 [[ ${codes[0]} == "$expected" && ${codes[1]} == 0 ]]
}
finish() {
 local status=$?
 local phase_status=$status
 trap - EXIT
 set +e
 (cd "$repo" && sha256sum --check "$reference") > "$out/final-source-guards.txt" 2>&1
 local guard=$?
 cmp "$reference" "$out/original-reference.sha256" >> "$out/final-source-guards.txt" 2>&1 || guard=1
 printf '%s\n' "$guard" > "$out/final-source-guards.exit"
 [[ $status -ne 0 || $guard -eq 0 ]] || status=$guard
 printf '%s\n' "$phase_status" > "$out/phase-caller.exit"
 printf '%s\n' "$status" > "$out/original.exit"
 date -u +%FT%TZ > "$out/finish.txt"
 exit "$status"
}
trap finish EXIT
date -u +%FT%TZ > "$out/start.txt"
git -C "$repo" rev-parse HEAD > "$out/consumer-head.txt"
git -C "$producer" rev-parse HEAD > "$out/producer-head.txt"
(cd "$repo" && sha256sum --check "$reference") > "$out/initial-source-guards.txt"
rustc -Vv > "$out/rustc.txt"
phase fetch 0 cargo fetch --locked --manifest-path "$manifest"
phase compile 0 timeout 900 cargo test --release --offline --locked --manifest-path "$manifest" --lib --no-run
phase native 0 bash -c 'ulimit -v 2097152; exec timeout 900 cargo test --release --offline --locked --manifest-path "$1" --lib -- --nocapture --test-threads=1' _ "$manifest"
grep -Eq '^test result: ok\. 3 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out;' "$out/native.txt"
phase bins 0 timeout 120 cargo build --release --offline --locked --manifest-path "$manifest" --bins
xz -dc "$ci/expected-native-02.json.xz" > "$out/expected-native.json"
xz -dc "$ci/legacy-native-04.json.xz" > "$out/legacy-native-04.json"
phase compare 0 bash -c '"$1/compare_native" "$2/expected-native.json" "$2/native.txt" "$2/all-native-records.json" && "$1/audit_accounting_change" "$2/legacy-native-04.json" "$2/all-native-records.json" "$2/accounting-change-audit.json"' _ "$CARGO_TARGET_DIR/release" "$out"
sed '/N4_BETA_ALL_EXCEPTIONAL /d' "$out/native.txt" > "$out/native-missing-exceptional.txt"
phase compare-negative 101 "$CARGO_TARGET_DIR/release/compare_native" "$out/expected-native.json" "$out/native-missing-exceptional.txt" "$out/omitted-record-must-not-accept.json"
[[ ! -e $out/omitted-record-must-not-accept.json ]] || exit 1
phase identity-issue 0 bash -c '"$1" > "$2"' _ "$CARGO_TARGET_DIR/release/crt_identity" "$out/identity.json"
cmp "$out/identity.json" "$repo/$study/beta-complete-evaluator/CRT-projection.certificate.json"
phase identity-replay 0 "$CARGO_TARGET_DIR/release/crt_identity" --verify "$out/identity.json"
phase identity-negative 101 "$CARGO_TARGET_DIR/release/crt_identity" --missing-linear-term
phase legacy-count-negative 101 "$CARGO_TARGET_DIR/release/legacy_count_control" --legacy-32-isogenies
mkdir -p "$producer/target"
[[ $(realpath -m "$producer/target") == "$producer/target" ]] || exit 2
stage=$(mktemp -d "$producer/target/complete-beta-proof-stage.XXXXXX")
modules=(CompleteRationalBeta CRTProjectionIdentity)
for name in "${modules[@]}"; do
 cp "$repo/$study/beta-complete-evaluator/lean/$name.lean" "$stage/$name.lean"
 cmp "$repo/$study/beta-complete-evaluator/lean/$name.lean" "$stage/$name.lean"
done
mkdir "$out/producer-staged-source"
cp "$stage/"*.lean "$out/producer-staged-source/"
sha256sum "$stage/"*.lean > "$out/producer-staging.sha256"
phase consumer-proof 0 env ELAN_TOOLCHAIN=leanprover/lean4:v4.34.1 bash "$repo/tools/lean/proof-gate.sh" --out "$out/consumer-proofs" "$study/beta-complete-evaluator/lean/CompleteRationalBeta.lean" "$study/beta-complete-evaluator/lean/CRTProjectionIdentity.lean"
phase producer-proof 0 bash -c 'cd "$1" && exec env ELAN_TOOLCHAIN=leanprover/lean4:v4.35.0 bash "$1/tools/lean/proof-gate.sh" --out "$2/producer-proofs" "$3/CompleteRationalBeta.lean" "$3/CRTProjectionIdentity.lean"' _ "$producer" "$out" "$stage"
for name in "${modules[@]}"; do cmp "$repo/$study/beta-complete-evaluator/lean/$name.lean" "$stage/$name.lean"; done
bindings=0
for index in beta-complete-rational-bindings-01 beta-CRT-projection-bindings-01; do
 while IFS= read -r claim; do
  bindings=$((bindings+1))
  phase "binding-$(basename "$claim" .json)" 0 env ELAN_TOOLCHAIN=leanprover/lean4:v4.34.1 python3 "$repo/tools/pcc/pcc.py" verify "$repo/$claim" --json
 done < <(jq -r '.[].claim_path' "$repo/$study/evidence/$index/claims.json")
done
[[ $bindings == 7 ]] || exit 1
for side in consumer producer; do
 grep -Eq "^PASS[[:space:]]+44[[:space:]]+thm[[:space:]]+0[[:space:]]+trusted.*CompleteRationalBeta" "$out/$side-proof.txt"
 grep -Eq "^PASS[[:space:]]+1[[:space:]]+thm[[:space:]]+0[[:space:]]+trusted.*CRTProjectionIdentity" "$out/$side-proof.txt"
done
phase final-guards 0 bash -c 'cd "$1" && sha256sum --check "$2"' _ "$repo" "$reference"
echo 'Complete rational beta replay: native3/all3wholeJSON/NOMASKS/exact accounting correction/two original44+1 gates/sevenbindings/threeactual101controls; unsigned conditional scope.'
