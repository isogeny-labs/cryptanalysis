#!/usr/bin/env bash
# Orchestration only; all research checks and whole-record comparisons use Rust/Lean.
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
cp "$0" "$out/original-command.sh"
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
packages=(nondual13-preflight nondual13-preflight/models nondual13-next-preflight nondual13-next-preflight/models)
labels=(second-edge second-model third-edge third-model)
for i in 0 1 2 3; do
 pkg=$repo/$study/${packages[$i]}
 label=${labels[$i]}
 [[ ! -e $pkg/generated ]] || exit 2
 phase "$label-materialize" 0 python3 "$pkg/materialize.py"
 cp "$pkg/generated/custody.json" "$out/$label-literal-custody.json"
 phase "$label-fetch" 0 timeout 120 cargo fetch --locked --manifest-path "$pkg/Cargo.toml"
 phase "$label-compile" 0 timeout 120 cargo test --release --locked --offline --manifest-path "$pkg/Cargo.toml" --lib --no-run --message-format=json
 python3 "$ci/capture_executable.py" "$out" "$label" compiled
 phase "$label-native" 0 bash -c 'ulimit -v 2097152; exec timeout 900 cargo test --release --locked --offline --manifest-path "$1" --lib -- --nocapture --test-threads=1' _ "$pkg/Cargo.toml"
 grep -Eq '^test result: ok\. 1 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out;' "$out/$label-native.txt"
 python3 "$ci/capture_executable.py" "$out" "$label" runtime
 if [[ $i != 3 ]]; then
  phase "$label-bins" 0 timeout 120 cargo build --release --locked --offline --manifest-path "$pkg/Cargo.toml" --bins
 fi
 xz -dc "$pkg/expected-native-01.json.xz" > "$out/$label-expected.json"
done
# Retain full binary bytes before any later invocation, with the original paths.
for bin in audit_native audit_models audit_records nondual13-old-dual-control next13-old-dual-control; do
 cp "$cache/release/$bin" "$out/$bin.actual-executable.bin"
done
sha256sum "$out"/*.actual-executable.bin > "$out/actual-bin-copies.sha256"
phase second-edge-compare 0 "$cache/release/audit_native" --compare "$out/second-edge-expected.json" "$out/second-edge-native.txt" "$out/second-edge-all-records.json"
phase second-model-compare 0 "$cache/release/audit_models" --compare "$out/second-model-expected.json" "$out/second-model-native.txt" "$out/second-model-all-records.json"
for kind in edge model; do
 phase "third-$kind-compare" 0 "$cache/release/audit_records" --compare "$kind" "$out/third-$kind-expected.json" "$out/third-$kind-native.txt" "$out/third-$kind-all-records.json"
done
# Delete actual entire native lines only; do not edit a JSON count or field.
sed '/N4_NONDUAL13_PUBLIC /d' "$out/second-edge-native.txt" > "$out/second-edge-whole-record-omitted.txt"
sed '/N4_NONDUAL13_MATCHED_MODELS /d' "$out/second-model-native.txt" > "$out/second-model-whole-record-omitted.txt"
sed '/N4_NEXT13_PUBLIC /d' "$out/third-edge-native.txt" > "$out/third-edge-whole-record-omitted.txt"
sed '/N4_NEXT13_MATCHED_MODELS /d' "$out/third-model-native.txt" > "$out/third-model-whole-record-omitted.txt"
phase second-edge-omission 101 "$cache/release/audit_native" --compare "$out/second-edge-expected.json" "$out/second-edge-whole-record-omitted.txt" "$out/second-edge-must-not-accept.json"
phase second-model-omission 101 "$cache/release/audit_models" --compare "$out/second-model-expected.json" "$out/second-model-whole-record-omitted.txt" "$out/second-model-must-not-accept.json"
for kind in edge model; do
 phase "third-$kind-omission" 101 "$cache/release/audit_records" --compare "$kind" "$out/third-$kind-expected.json" "$out/third-$kind-whole-record-omitted.txt" "$out/third-$kind-must-not-accept.json"
done
for label in "${labels[@]}"; do [[ ! -e $out/$label-must-not-accept.json ]] || exit 1; done
phase first-backtrack 101 bash -c 'ulimit -v 2097152; exec timeout 900 "$1"' _ "$out/nondual13-old-dual-control.actual-executable.bin"
phase first-backtrack-data 0 "$cache/release/audit_records" --old-control "$out/first-backtrack.txt" "$out/first-backtrack-all-records.json"
phase second-backtrack 101 bash -c 'ulimit -v 2097152; exec timeout 900 "$1"' _ "$out/next13-old-dual-control.actual-executable.bin"
phase second-backtrack-data 0 "$cache/release/audit_records" --control "$out/second-backtrack.txt" "$out/second-backtrack-all-records.json"
mkdir -p "$producer/target"
stage=$(mktemp -d "$producer/target/nondual-preflight-proof.XXXXXX")
cp "$repo/$study/nondual13-preflight/lean/NondualComposition.lean" "$stage/NondualComposition.lean"
cp "$repo/$study/nondual13-next-preflight/lean/NonsquareResidues.lean" "$stage/NonsquareResidues.lean"
cp -a "$stage" "$out/actual-proof-stage"
phase consumer-proof 0 env ELAN_TOOLCHAIN=leanprover/lean4:v4.34.1 bash tools/lean/proof-gate.sh --out "$out/consumer-proofs" "$study/nondual13-preflight/lean/NondualComposition.lean" "$study/nondual13-next-preflight/lean/NonsquareResidues.lean"
phase producer-proof 0 bash -c 'cd "$1" && exec env ELAN_TOOLCHAIN=leanprover/lean4:v4.35.0 bash tools/lean/proof-gate.sh --out "$2/producer-proofs" "$3/NondualComposition.lean" "$3/NonsquareResidues.lean"' _ "$producer" "$out" "$stage"
for claim in PCC-20261114-e90222 PCC-20261114-a76c1b PCC-20261114-ee88e7; do
 phase "binding-$claim" 0 env ELAN_TOOLCHAIN=leanprover/lean4:v4.34.1 python3 tools/pcc/pcc.py verify "pcc/claims/$claim.json" --json
done
phase final-guards 0 sha256sum --check "$reference"
echo 'Four unfiltered preflights, all4/6/5/9whole records, four whole-record101 controls, two actualbacktrack101 controls, original proofs and three bindings; unsigned finite/conditional scope.'
