#!/usr/bin/env bash
# Fresh exact-source replay. No mathematical computation in Python helpers.
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
reference=$ci/reference-03.sha256
cd "$repo"
cp "$reference" "$out/original-reference.sha256"
cp "$ci/check-03.sh" "$out/original-command.sh"
phase(){
 local name=$1 expected=$2;shift 2
 set +e
 "$@" 2>&1 | tee "$out/$name.txt"
 local codes=("${PIPESTATUS[@]}")
 set -e
 printf '%s %s\n' "${codes[0]}" "${codes[1]}" > "$out/$name.pipe-exits"
 printf '%s %s %s\n' "$name" "$expected" "${codes[0]}" >> "$out/phases.txt"
 [[ ${codes[0]} == "$expected" && ${codes[1]} == 0 ]]
}
finish(){
 local status=$?;trap - EXIT;set +e
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
phase initial-old-guards 0 sha256sum --check "$ci/reference-02.sha256"
phase initial-authored-guards 0 sha256sum --check "$ci/reference-03-authored.sha256"
geometry=$repo/$study/fixed-jacobian-chain-01
chain=$repo/$study/fixed-jacobian-chain-evaluator-01
for package in paired-fourth-preflight fixed-jacobian-chain-01 fixed-jacobian-chain-evaluator-01; do
 [[ ! -e $repo/$study/$package/generated ]] || exit 2
 phase "materialize-$package" 0 python3 "$repo/$study/$package/materialize.py"
 mkdir -p "$out/actual-compiled-source/$package"
 cp -aL "$repo/$study/$package/." "$out/actual-compiled-source/$package/"
 cp "$repo/$study/$package/generated/custody.json" "$out/$package-literal-custody.json"
done
cp -aL "$ci/audit" "$out/actual-compiled-source/geometry-auditor"
for package in "$geometry" "$chain" "$ci/audit"; do
 label=$(basename "$package")
 phase "fetch-$label" 0 timeout 120 cargo fetch --locked --manifest-path "$package/Cargo.toml"
done
phase install-literal-successors 0 python3 "$ci/install_sources_03.py" "$ci" "$repo/$study" "$out"
phase chain-metadata 0 timeout 120 cargo metadata --locked --offline --format-version=1 --manifest-path "$chain/Cargo.toml"
for package in fixed-jacobian-chain-evaluator-02 original-prime-chain-01 original-kernel-census-01 original-full-geometry-01 original-full-evaluator-01; do
 mkdir -p "$out/actual-compiled-source/$package"
 cp -aL "$repo/$study/$package/." "$out/actual-compiled-source/$package/"
 phase "fetch-$package" 0 timeout 120 cargo fetch --locked --manifest-path "$repo/$study/$package/Cargo.toml"
done
phase complete-successor-guards 0 sha256sum --check "$reference"
phase original-engine-preparation 0 timeout 900 cargo build --release --locked --offline --manifest-path "$chain/Cargo.toml" --package isogeny_algos --lib --message-format=json
python3 "$ci/capture_engine.py" "$out" "$producer" prepared
xz -dc "$geometry/../paired-fourth-preflight/expected-native-01.json.xz" > "$out/old-sixteen.json"
xz -dc "$geometry/expected-native-01.json.xz" > "$out/geometry-expected.json"
xz -dc "$chain/expected-native-01.json.xz" > "$out/chain-expected.json"
for label in geometry chain; do
 package=$geometry
 [[ $label == geometry ]] || package=$chain
 phase "$label-compile" 0 timeout 120 cargo test --release --locked --offline --manifest-path "$package/Cargo.toml" --lib --no-run --message-format=json
 python3 "$ci/capture_executable.py" "$out" "$label" compiled
 python3 "$ci/capture_engine.py" "$out" "$producer" reused "$label"
 phase "$label-native" 0 bash -c 'ulimit -v 2097152; exec timeout 900 cargo test --release --locked --offline --manifest-path "$1" --lib -- --nocapture --test-threads=1' _ "$package/Cargo.toml"
 grep -Eq '^test result: ok\. 1 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out;' "$out/$label-native.txt"
 python3 "$ci/capture_executable.py" "$out" "$label" runtime
 if [[ $label == geometry ]]; then
  auditor_manifest=$ci/audit/Cargo.toml
  auditor_name=audit-three-fixed-geometries
 else
  auditor_manifest=$chain/Cargo.toml
  auditor_name=audit-fixed-jacobian-chain
 fi
 phase "$label-auditor-compile" 0 timeout 120 cargo build --release --locked --offline --manifest-path "$auditor_manifest" --bin "$auditor_name" --message-format=json
 python3 "$ci/capture_auditor.py" "$out" compiled "$label-auditor" "$auditor_name"
 auditor=$(cat "$out/$label-auditor-actual-path.txt")
 phase "$label-whole-compare" 0 timeout 120 "$auditor" --compare "$out/old-sixteen.json" "$out/$label-expected.json" "$out/$label-native.txt" "$out/$label-all-whole-records.json"
 if [[ $label == geometry ]]; then
  tags=(N4_CHAIN_OLD_LITERAL_PARITY N4_CHAIN_FIXED_GEOMETRY)
 else
  tags=(N4_FIXED_CHAIN_EXCEPTIONAL_CASE N4_FIXED_CHAIN_ALL_EXCEPTIONALS N4_FIXED_CHAIN_ALL_PUBLIC N4_FIXED_CHAIN_SELECTED_CALL_VECTORS)
 fi
 for tag in "${tags[@]}"; do
  sed "/$tag /d" "$out/$label-native.txt" > "$out/$tag-entire-actual-records-omitted.txt"
  phase "$tag-omission" 101 timeout 120 "$auditor" --compare "$out/old-sixteen.json" "$out/$label-expected.json" "$out/$tag-entire-actual-records-omitted.txt" "$out/$tag-must-not-accept.json"
  [[ ! -e $out/$tag-must-not-accept.json ]] || exit 1
 done
 python3 "$ci/capture_auditor.py" "$out" runtime "$label-auditor" "$auditor_name"
done
# Additive workloads; all old phases and full record comparisons above remain.
phase successor-fixtures 0 python3 "$ci/fixtures_03.py" "$repo/$study" "$out"
export N4_ORIGINAL_PRIME_FIXTURES=$out/original-prime-fixtures
export N4_ORIGINAL_KERNEL_INPUTS=$out/original-kernel-fixtures
export N4_ORIGINAL_FULL_MODEL_FIXTURES=$out/original-geometry-fixtures
# This is the immutable original census experiment origin; current exact CI
# source revision is separately recorded in consumer-head.txt and source hashes.
export N4_ORIGINAL_KERNEL_SOURCE=811395139bbd33b75fd5697973202cd1dcc13bba
for label in norm-point original-prime original-kernel original-geometry original-full; do
 case "$label" in
  norm-point) package=fixed-jacobian-chain-evaluator-02; bin=audit-norm-point-reuse; fixture=$repo/$study/$package/expected-native-01.json.xz; encoding=xz; tags=(N4_FIXED_CHAIN_EXCEPTIONAL_CASE N4_FIXED_CHAIN_ALL_EXCEPTIONALS N4_FIXED_CHAIN_ALL_PUBLIC N4_FIXED_CHAIN_SELECTED_CALL_VECTORS);;
  original-prime) package=original-prime-chain-01; bin=audit-original-prime-chain; fixture=$repo/$study/$package/expected-native-02.json; encoding=plain; tags=(N4_ORIGINAL_PRIME_EXCEPTIONAL_CASE N4_ORIGINAL_PRIME_PUBLIC_CASE N4_ORIGINAL_PRIME_SOURCE_MODEL N4_ORIGINAL_PRIME_SELECTED_VECTORS);;
  original-kernel) package=original-kernel-census-01; bin=audit-original-kernel-census; fixture=$repo/$study/$package/expected-native-01.json; encoding=plain; tags=(N4_ORIGINAL_KERNEL_TRANSPORT N4_ORIGINAL_KERNEL_VERTEX N4_ORIGINAL_KERNEL_PAIR N4_ORIGINAL_KERNEL_TRIPLE);;
  original-geometry) package=original-full-geometry-01; bin=audit-original-full-geometry; fixture=$repo/$study/$package/expected-native-01.json; encoding=plain; tags=(N4_CHAIN_FIXED_GEOMETRY);;
  original-full) package=original-full-evaluator-01; bin=audit-original-full-chain; fixture=$repo/$study/$package/expected-native-02.json.xz; encoding=xz; tags=(N4_FIXED_CHAIN_EXCEPTIONAL_CASE N4_FIXED_CHAIN_ALL_EXCEPTIONALS N4_FIXED_CHAIN_ALL_PUBLIC N4_FIXED_CHAIN_SELECTED_CALL_VECTORS N4_ORIGINAL_FULL_KNOWN_POINT_VECTORS);;
 esac
 if [[ $encoding == xz ]]; then xz -dc "$fixture" > "$out/$label-expected.json"; else cp "$fixture" "$out/$label-expected.json"; fi
 manifest=$repo/$study/$package/Cargo.toml
 phase "$label-metadata" 0 timeout 120 cargo metadata --locked --offline --format-version=1 --manifest-path "$manifest"
 phase "$label-engine-closure" 0 python3 "$ci/engine_closure_03.py" "$out" "$producer" "$label"
 phase "$label-compile" 0 timeout 120 cargo test --release --locked --offline --manifest-path "$manifest" --lib --no-run --message-format=json
 python3 "$ci/capture_executable.py" "$out" "$label" compiled
 if [[ $label != original-kernel ]]; then python3 "$ci/capture_engine.py" "$out" "$producer" reused "$label"; fi
 phase "$label-native" 0 bash -c 'ulimit -v 2097152; exec timeout 900 cargo test --release --locked --offline --manifest-path "$1" --lib -- --nocapture --test-threads=1' _ "$manifest"
 grep -Eq '^test result: ok\. 1 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out;' "$out/$label-native.txt"
 python3 "$ci/capture_executable.py" "$out" "$label" runtime
 if [[ $label != original-kernel ]]; then
  cp "$out/engine-reused-$label.json" "$out/engine-reused-$label-before-native.json"
  python3 "$ci/capture_engine.py" "$out" "$producer" reused "$label"
 fi
 phase "$label-auditor-compile" 0 timeout 120 cargo build --release --locked --offline --manifest-path "$manifest" --bin "$bin" --message-format=json
 python3 "$ci/capture_auditor.py" "$out" compiled "$label-auditor" "$bin"
 auditor=$(cat "$out/$label-auditor-actual-path.txt")
 prefix=("$out/old-sixteen.json")
 [[ $label != original-kernel ]] || prefix=()
 [[ $label != original-geometry ]] || prefix+=("$out/geometry-expected.json")
 phase "$label-whole-compare" 0 timeout 120 "$auditor" --compare "${prefix[@]}" "$out/$label-expected.json" "$out/$label-native.txt" "$out/$label-all-whole-records.json"
 for tag in "${tags[@]}"; do
  sed "/$tag /d" "$out/$label-native.txt" > "$out/$label-$tag-entire-actual-records-omitted.txt"
  phase "$label-$tag-omission" 101 timeout 120 "$auditor" --compare "${prefix[@]}" "$out/$label-expected.json" "$out/$label-$tag-entire-actual-records-omitted.txt" "$out/$label-$tag-must-not-accept.json"
  [[ ! -e $out/$label-$tag-must-not-accept.json ]] || exit 1
 done
 python3 "$ci/capture_auditor.py" "$out" runtime "$label-auditor" "$bin"
done
mkdir -p "$producer/target"
stage=$(mktemp -d "$producer/target/complete-fixed-chain-proof.XXXXXX")
consumer_paths=()
producer_paths=()
for module in twisted-pair-preflight/lean/TwistHomogeneity twisted-pair-preflight/lean/TwistingFactor twisted-pair-preflight/lean/OldPrimeObstruction paired-fourth-preflight/lean/ThreePairNorm paired-fourth-preflight/lean/FourthObstruction fixed-jacobian-chain-evaluator-01/lean/ChainDescent fixed-jacobian-chain-evaluator-01/lean/FullGroupNorm fixed-jacobian-chain-evaluator-02/lean/NormPointReuse original-prime-chain-01/lean/PrimeReprojection original-kernel-census-01/lean/KernelCensus original-full-evaluator-01/lean/OriginalFullChain original-full-evaluator-01/lean/PrimeRecovery; do
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
done < "$ci/statement-bindings-03.txt"
phase final-guards 0 sha256sum --check "$reference"
echo 'Seven unfiltered tests; all13+695+695+1077+311+16+701 whole records,24 actual whole-class omissions101/no output, both original70-root gates/all70 exact bindings. Full source/fixtures/compiler-runtime/prepared-byte custody. Unsigned and unpriced replay only.'
