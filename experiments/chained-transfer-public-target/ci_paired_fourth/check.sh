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
pkg=$repo/$study/paired-fourth-preflight
[[ ! -e $pkg/generated ]] || exit 2
phase materialize 0 python3 "$pkg/materialize.py"
cp "$pkg/generated/custody.json" "$out/literal-source-custody.json"
cp -aL "$pkg" "$out/actual-compiled-source"
phase fetch 0 timeout 120 cargo fetch --locked --manifest-path "$pkg/Cargo.toml"
# Existing prospective f10846: explicit package preparation, then bounded wrapper.
# This does not discharge the historical full cold120 compilation requirement.
phase original-engine-preparation 0 timeout 900 cargo build --release --locked --offline --manifest-path "$pkg/Cargo.toml" --package isogeny_algos --lib --message-format=json
python3 "$ci/capture_engine.py" "$out" "$producer" prepared
phase paired-fourth-compile 0 timeout 120 cargo test --release --locked --offline --manifest-path "$pkg/Cargo.toml" --lib --no-run --message-format=json
python3 "$ci/capture_executable.py" "$out" paired-fourth compiled
python3 "$ci/capture_engine.py" "$out" "$producer" reused
phase paired-fourth-native 0 bash -c 'ulimit -v 2097152; exec timeout 900 cargo test --release --locked --offline --manifest-path "$1" --lib -- --nocapture --test-threads=1' _ "$pkg/Cargo.toml"
grep -Eq '^test result: ok\. 1 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out;' "$out/paired-fourth-native.txt"
python3 "$ci/capture_executable.py" "$out" paired-fourth runtime
phase auditor-compile 0 timeout 120 cargo build --release --locked --offline --manifest-path "$pkg/Cargo.toml" --bin audit-paired-fourth --message-format=json
python3 "$ci/capture_auditor.py" "$out" compiled
auditor=$(cat "$out/auditor-actual-path.txt")
xz -dc "$pkg/../twisted-pair-preflight/expected-native-02.json.xz" > "$out/old-nine-expected.json"
xz -dc "$pkg/expected-native-01.json.xz" > "$out/all-sixteen-expected.json"
phase whole-sixteen-compare 0 "$auditor" --compare "$out/old-nine-expected.json" "$out/all-sixteen-expected.json" "$out/paired-fourth-native.txt" "$out/all-sixteen-whole-records.json"
for tag in N4_FOURTH_PUBLIC N4_FOURTH_MATCHED_ENDPOINTS; do
 sed "/$tag /d" "$out/paired-fourth-native.txt" > "$out/$tag-entire-actual-record-omitted.txt"
 phase "$tag-omission" 101 "$auditor" --compare "$out/old-nine-expected.json" "$out/all-sixteen-expected.json" "$out/$tag-entire-actual-record-omitted.txt" "$out/$tag-must-not-accept.json"
 [[ ! -e $out/$tag-must-not-accept.json ]] || exit 1
done
phase old-dual-compile 0 timeout 120 cargo build --release --locked --offline --manifest-path "$pkg/Cargo.toml" --bin paired-fourth-old-dual-control --message-format=json
python3 "$ci/capture_control.py" "$out" compiled
control=$(cat "$out/control-actual-path.txt")
phase actual-old-third-dual 101 bash -c 'ulimit -v 2097152; exec timeout 900 "$1"' _ "$control"
phase old-dual-whole-five 0 "$auditor" --control "$out/old-nine-expected.json" "$out/actual-old-third-dual.txt" "$out/all-five-old-dual-control-records.json"
xz -dc "$pkg/expected-old-dual-control-01.json.xz" > "$out/whole-five-original-control.json"
phase all-five-control-exact-bytes 0 cmp "$out/whole-five-original-control.json" "$out/all-five-old-dual-control-records.json"
python3 "$ci/capture_control.py" "$out" runtime
python3 "$ci/capture_auditor.py" "$out" runtime
mkdir -p "$producer/target"
stage=$(mktemp -d "$producer/target/paired-fourth-proof.XXXXXX")
consumer_paths=()
producer_paths=()
for module in twisted-pair-preflight/lean/TwistHomogeneity twisted-pair-preflight/lean/TwistingFactor twisted-pair-preflight/lean/OldPrimeObstruction paired-fourth-preflight/lean/ThreePairNorm paired-fourth-preflight/lean/FourthObstruction; do
 name=${module##*/}
 cp "$repo/$study/$module.lean" "$stage/$name.lean"
 consumer_paths+=("$study/$module.lean")
 producer_paths+=("$stage/$name.lean")
done
cp -a "$stage" "$out/actual-proof-stage"
phase consumer-proof 0 env ELAN_TOOLCHAIN=leanprover/lean4:v4.34.1 bash tools/lean/proof-gate.sh --out "$out/consumer-proofs" "${consumer_paths[@]}"
phase producer-proof 0 bash -c 'cd "$1"; shift; exec env ELAN_TOOLCHAIN=leanprover/lean4:v4.35.0 bash tools/lean/proof-gate.sh "$@"' _ "$producer" --out "$out/producer-proofs" "${producer_paths[@]}"
while IFS= read -r claim; do
 phase "binding-$claim" 0 env ELAN_TOOLCHAIN=leanprover/lean4:v4.34.1 python3 tools/pcc/pcc.py verify "pcc/claims/$claim.json" --json
done < "$ci/statement-bindings-01.txt"
phase final-guards 0 sha256sum --check "$reference"
echo 'One unfiltered paired-fourth preflight; all sixteen whole ordered records including all nine prior records; two actual whole-record omissions101; actual old-third-dual101 and exact five-record data; both original proof gates and twenty exact local bindings. Unsigned finite and conditional scope.'
