#!/usr/bin/env bash
# Additive exact-source replay of frozen IC/sampler protocols; all mathematics is Rust/Lean.
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
export RUSTUP_TOOLCHAIN=1.99.1 CARGO_TARGET_DIR=$cache
base_ci=$repo/$study/ci_fixed_chain
reference=$ci/reference-01.sha256
cd "$repo"
cp "$reference" "$out/original-reference.sha256"
cp "$ci/check-01.sh" "$out/original-command.sh"
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
phase initial-original-guards 0 sha256sum --check "$base_ci/reference-02.sha256"
for package in paired-fourth-preflight fixed-jacobian-chain-01 fixed-jacobian-chain-evaluator-01; do
 [[ ! -e $repo/$study/$package/generated ]] || exit 2
 phase "materialize-$package" 0 python3 "$repo/$study/$package/materialize.py"
 mkdir -p "$out/actual-compiled-source/$package"
 cp -aL "$repo/$study/$package/." "$out/actual-compiled-source/$package/"
done
phase install-literal-successors 0 python3 "$base_ci/install_sources_03.py" "$base_ci" "$repo/$study" "$out"
chain=$repo/$study/fixed-jacobian-chain-evaluator-01
for package in fixed-jacobian-chain-evaluator-01 original-fixed-model-ic-01 original-fixed-model-sampler-01 ci_original_fixed_ic/audit; do
 fetch_label=${package//\//-}
 phase "fetch-$fetch_label" 0 timeout 120 cargo fetch --locked --manifest-path "$repo/$study/$package/Cargo.toml"
done
phase chain-metadata 0 timeout 120 cargo metadata --locked --offline --format-version=1 --manifest-path "$chain/Cargo.toml"
phase complete-original1440-guards 0 sha256sum --check "$base_ci/reference-03.sha256"
phase complete-sampler1487-guards 0 sha256sum --check "$repo/$study/original-fixed-model-sampler-01/frozen-prior-inputs-01.sha256"
phase authored-and-fixture-guards 0 sha256sum --check "$reference"
phase original-engine-preparation 0 timeout 900 cargo build --release --locked --offline --manifest-path "$chain/Cargo.toml" --package isogeny_algos --lib --message-format=json
python3 "$base_ci/capture_engine.py" "$out" "$producer" prepared
cp -aL "$ci/audit" "$out/actual-compiled-source/historical-auditor"
phase historical-auditor-compile 0 timeout 120 cargo build --release --locked --offline --manifest-path "$ci/audit/Cargo.toml" --bin audit-original-fixed-ic-historical --message-format=json
python3 "$base_ci/capture_auditor.py" "$out" compiled historical-auditor audit-original-fixed-ic-historical
historical=$(cat "$out/historical-auditor-actual-path.txt")
for label in original-ic original-sampler; do
 case "$label" in
  original-ic) package=original-fixed-model-ic-01;bin=audit-original-fixed-model-ic;tags=(N4_ORIGINAL_MODEL_IC_SETUP N4_ORIGINAL_MODEL_IC_INPUT N4_ORIGINAL_MODEL_IC_ATTEMPT N4_ORIGINAL_MODEL_IC_CASE N4_ORIGINAL_MODEL_IC_REJECTIONS N4_ORIGINAL_MODEL_IC_TARGET N4_ORIGINAL_MODEL_IC_SCOPE);;
  original-sampler) package=original-fixed-model-sampler-01;bin=audit-original-fixed-model-sampler;tags=(N4_ORIGINAL_FIXED_SAMPLER_SETUP N4_ORIGINAL_FIXED_SAMPLER_PROVENANCE N4_ORIGINAL_FIXED_SAMPLER_INPUT N4_ORIGINAL_FIXED_SAMPLER_SCALARS N4_ORIGINAL_FIXED_SAMPLER_ATTEMPT N4_ORIGINAL_FIXED_SAMPLER_CASE N4_ORIGINAL_FIXED_SAMPLER_TARGET N4_ORIGINAL_FIXED_SAMPLER_SCOPE);;
 esac
 manifest=$repo/$study/$package/Cargo.toml
 mkdir -p "$out/actual-compiled-source/$package"
 cp -aL "$repo/$study/$package/." "$out/actual-compiled-source/$package/"
 xz -dc "$repo/$study/$package/expected-native-01.json.xz" > "$out/$label-expected.json"
 phase "$label-metadata" 0 timeout 120 cargo metadata --locked --offline --format-version=1 --manifest-path "$manifest"
 phase "$label-engine-closure" 0 python3 "$base_ci/engine_closure_03.py" "$out" "$producer" "$label"
 phase "$label-compile" 0 timeout 120 cargo test --release --locked --offline --manifest-path "$manifest" --lib --no-run --message-format=json
 python3 "$base_ci/capture_executable.py" "$out" "$label" compiled
 python3 "$base_ci/capture_engine.py" "$out" "$producer" reused "$label"
 phase "$label-native" 0 bash -c 'ulimit -v 2097152;exec timeout 900 cargo test --release --locked --offline --manifest-path "$1" --lib -- --nocapture --test-threads=1' _ "$manifest"
 grep -Eq '^test result: ok\. 1 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out;' "$out/$label-native.txt"
 python3 "$base_ci/capture_executable.py" "$out" "$label" runtime
 cp "$out/engine-reused-$label.json" "$out/engine-reused-$label-before-native.json"
 python3 "$base_ci/capture_engine.py" "$out" "$producer" reused "$label"
 phase "$label-auditor-compile" 0 timeout 120 cargo build --release --locked --offline --manifest-path "$manifest" --bin "$bin" --message-format=json
 python3 "$base_ci/capture_auditor.py" "$out" compiled "$label-auditor" "$bin"
 auditor=$(cat "$out/$label-auditor-actual-path.txt")
 phase "$label-whole-freeze" 0 timeout 120 "$auditor" --freeze "$out/$label-native.txt" "$out/$label-whole-frozen.json"
 phase "$label-whole-same-run-compare" 0 timeout 120 "$auditor" --compare "$out/$label-whole-frozen.json" "$out/$label-native.txt" "$out/$label-all-whole-records.json"
 phase "$label-whole-historical-compare" 0 timeout 120 "$historical" --compare "$label" "$out/$label-expected.json" "$out/$label-whole-frozen.json" "$out/$label-historical-equality.json"
 phase "$label-whole-freeze-compare" 0 cmp "$out/$label-whole-frozen.json" "$out/$label-all-whole-records.json"
 phase "$label-historical-controls-materialize" 0 timeout 120 "$historical" --mutations "$label" "$out/$label-expected.json" "$out/$label-historical-controls"
 for control in missing-record-class changed-scalar changed-counter unexpected-report-field timing-only; do
  expected_exit=1
  [[ $control != timing-only ]] || expected_exit=0
  accepted=$out/$label-$control-historical-accepted.json
  phase "$label-historical-$control" "$expected_exit" timeout 120 "$historical" --compare "$label" "$out/$label-historical-controls/$control.json" "$out/$label-whole-frozen.json" "$accepted"
  if [[ $expected_exit == 1 ]]; then [[ ! -e $accepted ]] || exit 1; else [[ -f $accepted ]] || exit 1; fi
 done
 python3 "$base_ci/capture_auditor.py" "$out" runtime historical-auditor audit-original-fixed-ic-historical
 for tag in "${tags[@]}"; do
  omitted=$out/$label-$tag-entire-actual-records-omitted.txt.xz
  phase "$label-$tag-materialize-XZ" 0 bash -o pipefail -c 'sed "/$1 /d" "$2" | xz -c > "$3"' _ "$tag" "$out/$label-native.txt" "$omitted"
  phase "$label-$tag-whole-XZ-CRC" 0 xz --test "$omitted"
  phase "$label-$tag-omission" 101 bash -c 'exec timeout 120 "$1" --compare "$2" <(xz -dc "$3") "$4"' _ "$auditor" "$out/$label-whole-frozen.json" "$omitted" "$out/$label-$tag-must-not-accept.json"
  [[ ! -e $out/$label-$tag-must-not-accept.json ]] || exit 1
 done
 python3 "$base_ci/capture_auditor.py" "$out" runtime "$label-auditor" "$bin"
 phase "$label-whole-omission-custody" 0 python3 "$ci/check_omissions_01.py" "$out" "$label" "${tags[@]}"
done
mkdir -p "$producer/target"
stage=$(mktemp -d "$producer/target/original-fixed-IC-proof.XXXXXX")
modules=(new-target-ic/lean/NewTargetIC norm-assisted-ic/lean/NormAssistedSampling)
consumer_paths=();producer_paths=()
for module in "${modules[@]}"; do
 name=${module##*/};cp "$repo/$study/$module.lean" "$stage/$name.lean"
 consumer_paths+=("$study/$module.lean");producer_paths+=("$stage/$name.lean")
done
cp -a "$stage" "$out/actual-proof-stage"
phase consumer-five-root-proof 0 env ELAN_TOOLCHAIN=leanprover/lean4:v4.34.1 bash tools/lean/proof-gate.sh --out "$out/consumer-proofs" "${consumer_paths[@]}"
phase producer-five-root-proof 0 bash -c 'cd "$1";shift;exec env ELAN_TOOLCHAIN=leanprover/lean4:v4.35.0 bash tools/lean/proof-gate.sh "$@"' _ "$producer" --out "$out/producer-proofs" "${producer_paths[@]}"
while IFS= read -r claim; do
 phase "binding-$claim" 0 env ELAN_TOOLCHAIN=leanprover/lean4:v4.34.1 python3 tools/pcc/pcc.py verify "pcc/claims/$claim.json" --json
done < "$ci/statement-bindings-01.txt"
phase induced-full-transfer-proof 0 bash "$repo/$study/ci_induced_transfer/check-01.sh" "$producer" "$out/induced-full-transfer-proof"
phase complete-receipt-validation 0 python3 "$ci/validate_receipts_01.py" "$repo" "$out"
phase final-source-guards 0 sha256sum --check "$reference"
echo 'Two complete unfiltered tests; entire historical100/101 populations; fifteen actual whole-class omissions101/no output; original proof gates/bindings and induced proof replay; exact source/runtime/full-prepared custody. Unsigned correctness replay, no calibrated timing claim.'
