#!/usr/bin/env bash
# Native Rust/Lean checks; Python is limited to materialization and byte custody.
set -euo pipefail
[[ $# == 2 ]] || exit 2
ci=$(cd -- "$(dirname -- "$0")" && pwd -P)
repo=$(git -C "$ci" rev-parse --show-toplevel)
producer=$(cd -- "$1" && pwd -P)
out=$(realpath -m "$2")
cache=${out}-build-cache
[[ ! -e $out && ! -e $cache ]] || exit 2
[[ $(realpath -m "$repo/../crypto") == "$producer" ]] || exit 2
case "$out/" in "$repo/"*|"$producer/"*) exit 2;; esac
for tool in cargo rustc lean lake python3 jq xz; do command -v "$tool" >/dev/null || exit 2; done
study=experiments/chained-transfer-public-target
[[ $(git -C "$producer" rev-parse HEAD) == "$(cat "$repo/$study/upstream-commit.txt")" ]] || exit 2
mkdir "$out"
export RUSTUP_TOOLCHAIN=1.99.1
export CARGO_TARGET_DIR=$cache
reference=$ci/reference-01.sha256
cd "$repo"
cp "$reference" "$out/original-reference.sha256"
cp "$ci/check.sh" "$out/original-command.sh"
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
 trap - EXIT
 set +e
 sha256sum --check "$reference" > "$out/final-source-guards.txt" 2>&1
 local guard=$?
 cmp "$reference" "$out/original-reference.sha256" >> "$out/final-source-guards.txt" 2>&1 || guard=1
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
rustc -Vv > "$out/rustc.txt"
phase initial-guards 0 sha256sum --check "$reference"
pkg=$repo/$study/twisted-pair-preflight
[[ ! -e $pkg/generated ]] || exit 2
phase materialize 0 python3 "$pkg/materialize.py"
cp "$pkg/generated/custody.json" "$out/literal-source-custody.json"
cp -aL "$pkg" "$out/actual-compiled-source"
phase fetch 0 timeout 120 cargo fetch --locked --manifest-path "$pkg/Cargo.toml"
# Existing prospective f10846: explicit package preparation, then bounded wrapper.
# This does not discharge the historical full cold120 compilation requirement.
phase original-engine-preparation 0 timeout 900 cargo build --release --locked --offline --manifest-path "$pkg/Cargo.toml" --package isogeny_algos --lib --message-format=json
python3 "$ci/capture_engine.py" "$out" "$producer" prepared
phase fixed-pair-compile 0 timeout 120 cargo test --release --locked --offline --manifest-path "$pkg/Cargo.toml" --lib --no-run --message-format=json
python3 "$ci/capture_executable.py" "$out" fixed-pair compiled
python3 "$ci/capture_engine.py" "$out" "$producer" reused
phase fixed-pair-native 0 bash -c 'ulimit -v 2097152; exec timeout 900 cargo test --release --locked --offline --manifest-path "$1" --lib -- --nocapture --test-threads=1' _ "$pkg/Cargo.toml"
grep -Eq '^test result: ok\. 1 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out;' "$out/fixed-pair-native.txt"
python3 "$ci/capture_executable.py" "$out" fixed-pair runtime
phase auditor-compile 0 timeout 120 cargo build --release --locked --offline --manifest-path "$pkg/Cargo.toml" --bin audit-twisted-pair --message-format=json
python3 "$ci/capture_auditor.py" "$out" compiled
auditor=$(cat "$out/auditor-actual-path.txt")
xz -dc "$pkg/expected-native-02.json.xz" > "$out/fixed-pair-expected.json"
phase whole-nine-compare 0 "$auditor" --compare "$out/fixed-pair-expected.json" "$out/fixed-pair-native.txt" "$out/all-nine-whole-records.json"
sed '/N4_TWIST_MATCHED_PAIR /d' "$out/fixed-pair-native.txt" > "$out/actual-entire-matched-pair-omitted.txt"
phase whole-matched-pair-omission 101 "$auditor" --compare "$out/fixed-pair-expected.json" "$out/actual-entire-matched-pair-omitted.txt" "$out/must-not-accept.json"
[[ ! -e $out/must-not-accept.json ]] || exit 1
python3 "$ci/capture_auditor.py" "$out" runtime
mkdir -p "$producer/target"
stage=$(mktemp -d "$producer/target/fixed-twisted-pair-proof.XXXXXX")
proofs=(TwistHomogeneity TwistingFactor OldPrimeObstruction)
consumer_paths=()
producer_paths=()
for name in "${proofs[@]}"; do
 cp "$pkg/lean/$name.lean" "$stage/$name.lean"
 consumer_paths+=("$study/twisted-pair-preflight/lean/$name.lean")
 producer_paths+=("$stage/$name.lean")
done
cp -a "$stage" "$out/actual-proof-stage"
phase consumer-proof 0 env ELAN_TOOLCHAIN=leanprover/lean4:v4.34.1 bash tools/lean/proof-gate.sh --out "$out/consumer-proofs" "${consumer_paths[@]}"
phase producer-proof 0 bash -c 'cd "$1"; shift; exec env ELAN_TOOLCHAIN=leanprover/lean4:v4.35.0 bash tools/lean/proof-gate.sh "$@"' _ "$producer" --out "$out/producer-proofs" "${producer_paths[@]}"
while IFS= read -r claim; do
 phase "binding-$claim" 0 env ELAN_TOOLCHAIN=leanprover/lean4:v4.34.1 python3 tools/pcc/pcc.py verify "pcc/claims/$claim.json" --json
done < "$ci/statement-bindings-01.txt"
phase final-guards 0 sha256sum --check "$reference"
echo 'One unfiltered fixed-pair preflight; all nine whole ordered records/no masks/no dedup; actual entire matched-pair omission101; both original proof gates and fourteen exact local bindings. Unsigned finite/conditional scope.'
