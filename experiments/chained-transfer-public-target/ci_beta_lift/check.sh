#!/usr/bin/env bash
# Thin orchestration; all mathematical/replay work is native Rust/Lean.
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
mkdir "$out"
export RUSTUP_TOOLCHAIN=1.99.1
export CARGO_TARGET_DIR=$cache
cd "$repo"
study=experiments/chained-transfer-public-target
manifest=$repo/$study/beta-rational-lift/Cargo.toml
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
[[ $(realpath -m "$repo/../crypto") == "$producer" ]] || exit 2
(cd "$repo" && sha256sum --check "$reference") > "$out/initial-source-guards.txt"
rustc -Vv > "$out/rustc.txt"
phase fetch 0 cargo fetch --locked --manifest-path "$manifest"
phase compile 0 timeout 900 cargo test --release --offline --locked --manifest-path "$manifest" --lib --no-run
phase native 0 bash -c 'ulimit -v 2097152; exec timeout 900 cargo test --release --offline --locked --manifest-path "$1" --lib -- --nocapture --test-threads=1' _ "$manifest"
grep -Eq '^test result: ok\. 2 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out;' "$out/native.txt"
phase bins 0 timeout 120 cargo build --release --offline --locked --manifest-path "$manifest" --bins
xz -dc "$ci/expected-native-01.json.xz" > "$out/expected-native.json"
phase compare 0 "$CARGO_TARGET_DIR/release/compare_native" "$out/expected-native.json" "$out/native.txt" "$out/all-native-records.json"
phase identity-issue 0 bash -c '"$1" > "$2"' _ "$CARGO_TARGET_DIR/release/quadratic_identity" "$out/identity.json"
cmp "$out/identity.json" "$repo/$study/beta-rational-lift/quadratic-norm.certificate.json"
phase identity-replay 0 "$CARGO_TARGET_DIR/release/quadratic_identity" --verify "$out/identity.json"
phase identity-negative 101 "$CARGO_TARGET_DIR/release/quadratic_identity" --missing-imaginary-term
mkdir -p "$producer/target"
[[ $(realpath -m "$producer/target") == "$producer/target" ]] || exit 2
stage=$(mktemp -d "$producer/target/beta-proof-stage.XXXXXX")
modules=(QuadraticRationalLift QuadraticNormIdentity)
for name in "${modules[@]}"; do
 cp "$repo/$study/beta-rational-lift/lean/$name.lean" "$stage/$name.lean"
 cmp "$repo/$study/beta-rational-lift/lean/$name.lean" "$stage/$name.lean"
done
mkdir "$out/producer-staged-source"
cp "$stage/"*.lean "$out/producer-staged-source/"
sha256sum "$stage/"*.lean > "$out/producer-staging.sha256"
phase consumer-proof 0 env ELAN_TOOLCHAIN=leanprover/lean4:v4.34.1 bash "$repo/tools/lean/proof-gate.sh" --out "$out/consumer-proofs" "$study/beta-rational-lift/lean/QuadraticRationalLift.lean" "$study/beta-rational-lift/lean/QuadraticNormIdentity.lean"
phase producer-proof 0 env ELAN_TOOLCHAIN=leanprover/lean4:v4.35.0 bash "$producer/tools/lean/proof-gate.sh" --out "$out/producer-proofs" "$stage/QuadraticRationalLift.lean" "$stage/QuadraticNormIdentity.lean"
for name in "${modules[@]}"; do cmp "$repo/$study/beta-rational-lift/lean/$name.lean" "$stage/$name.lean"; done
bindings=0
for index in beta-rational-lift-bindings-01 beta-quadratic-norm-bindings-01; do
 while IFS= read -r claim; do
  bindings=$((bindings+1))
  phase "binding-$(basename "$claim" .json)" 0 env ELAN_TOOLCHAIN=leanprover/lean4:v4.34.1 python3 "$repo/tools/pcc/pcc.py" verify "$repo/$claim" --json
 done < <(jq -r '.[].claim_path' "$repo/$study/evidence/$index/claims.json")
done
[[ $bindings == 6 ]] || exit 1
for side in consumer producer; do
 grep -Eq "^PASS[[:space:]]+20[[:space:]]+thm[[:space:]]+0[[:space:]]+trusted.*QuadraticRationalLift" "$out/$side-proof.txt"
 grep -Eq "^PASS[[:space:]]+1[[:space:]]+thm[[:space:]]+0[[:space:]]+trusted.*QuadraticNormIdentity" "$out/$side-proof.txt"
done
phase final-guards 0 bash -c 'cd "$1" && sha256sum --check "$2"' _ "$repo" "$reference"
echo 'Actual beta rational-lift/field replay complete: native2/all3wholeJSON/NOMASKS/IDCpositive0negative101/twooriginalproofgates21declarations0trusted/sixexactbindings; finite conditional scope, unsigned.'
