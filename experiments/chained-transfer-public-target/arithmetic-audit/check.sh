#!/usr/bin/env bash
# Thin build/run orchestration; all arithmetic/controls/record comparison are Rust.
set -euo pipefail
[[ $# == 3 ]] || exit 2
audit=$(cd -- "$(dirname -- "$0")" && pwd -P)
consumer=$(cd -- "$1" && pwd -P)
producer=$(cd -- "$2" && pwd -P)
out=$(realpath -m "$3")
audit_repo=$(git -C "$audit" rev-parse --show-toplevel)
layout=${out}-layout
cache=${out}-build-cache
[[ ! -e $out && ! -e $layout && ! -e $cache ]] || exit 2
case "$out/" in "$consumer/"*|"$producer/"*|"$audit_repo/"*) exit 2;; esac
mkdir "$out"
export RUSTUP_TOOLCHAIN=1.99.1
export CARGO_TARGET_DIR=$cache
study=experiments/chained-transfer-public-target
reference=$audit/reference-03.sha256
solver=$layout/derived-layout/cryptanalysis/$study/norm-assisted-ic/Cargo.toml
taps=$layout/derived-layout/n4-arithmetic-taps/Cargo.toml
phase() {
 local label=$1; shift
 set +e
 "$@" 2>&1 | tee "$out/$label.txt"
 local codes=("${PIPESTATUS[@]}")
 set -e
 printf '%s %s\n' "${codes[0]}" "${codes[1]}" > "$out/$label.pipe-exits"
 printf '%s %s\n' "$label" "${codes[0]}" >> "$out/phases.txt"
 [[ ${codes[0]} == 0 && ${codes[1]} == 0 ]]
}
finish() {
 local status=$?
 local phase_status=$status
 trap - EXIT
 set +e
 (cd "$audit_repo" && sha256sum --check "$reference") > "$out/final-audit-source.txt" 2>&1
 source_status=$?
 cmp "$reference" "$out/audit-source-manifest-original.sha256" >> "$out/final-audit-source.txt" 2>&1 || source_status=1
 printf '%s\n' "$source_status" > "$out/final-audit-source.exit"
 [[ $status -ne 0 || $source_status -eq 0 ]] || status=$source_status
 if [[ -f $layout/original-785.sha256 ]]; then
  (cd "$layout/original-layout" && sha256sum --check "$layout/original-785.sha256") > "$out/final-original-785.txt" 2>&1
  original_status=$?
  printf '%s\n' "$original_status" > "$out/final-original-785.exit"
  [[ $status -ne 0 || $original_status -eq 0 ]] || status=$original_status
 fi
 if [[ -f $out/derived-before.sha256 ]]; then
  (cd "$layout/derived-layout" && sha256sum --check "$out/derived-before.sha256") > "$out/final-derived.txt" 2>&1
  derived_status=$?
  printf '%s\n' "$derived_status" > "$out/final-derived.exit"
  [[ $status -ne 0 || $derived_status -eq 0 ]] || status=$derived_status
 fi
 printf '%s\n' "$phase_status" > "$out/phase-caller.exit"
 printf '%s\n' "$status" > "$out/original.exit"
 date -u +%FT%TZ > "$out/finish.txt"
 exit "$status"
}
trap finish EXIT
date -u +%FT%TZ > "$out/start.txt"
rustc -Vv > "$out/rustc.txt"
cp "$reference" "$out/audit-source-manifest-original.sha256"
(cd "$audit_repo" && sha256sum --check "$reference") > "$out/initial-audit-source.txt"
phase materialize bash "$audit/materialize.sh" "$consumer" "$producer" "$layout"
phase fetch-original cargo fetch --locked --manifest-path "$layout/original-layout/cryptanalysis/$study/norm-assisted-ic/Cargo.toml"
phase lock-solver cargo metadata --offline --format-version 1 --manifest-path "$solver"
phase fetch-taps cargo fetch --locked --manifest-path "$taps"
phase lock-taps cargo metadata --offline --locked --format-version 1 --manifest-path "$taps"
# Preserve all registry blocks exactly, including names/versions/checksums/dependencies.
for arm in original derived; do
 awk 'BEGIN { RS="\n\\[\\[package\\]\\]\n" } /source = / { print }' "$layout/$arm-layout/cryptanalysis/$study/norm-assisted-ic/Cargo.lock" > "$out/$arm-registry-lock-blocks.txt"
done
phase frozen-registry cmp "$out/original-registry-lock-blocks.txt" "$out/derived-registry-lock-blocks.txt"
(cd "$layout/derived-layout" && find . -type f -print0 | sort -z | xargs -0 sha256sum) > "$out/derived-before.sha256"
phase compile timeout 900 cargo test --release --offline --locked --manifest-path "$solver" --lib --no-run
phase native bash -c 'ulimit -v 2097152; exec timeout 900 cargo test --release --offline --locked --manifest-path "$1" --lib -- --nocapture --test-threads=1' _ "$solver"
grep -Eq '^test result: ok\. 1 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out;' "$out/native.txt"
phase ledger-unit timeout 120 cargo test --release --offline --locked --manifest-path "$taps" --lib -- --nocapture --test-threads=1
phase compare-build timeout 120 cargo build --release --offline --locked --manifest-path "$taps" --bin compare
xz -dc "$layout/original-layout/cryptanalysis/$study/ci_norm_sampling/expected-native.json.xz" > "$out/expected-native.json"
phase all86 "$cache/release/compare" "$out/expected-native.json" "$out/native.txt" "$out/all-native-records.json"
phase census-build timeout 120 cargo build --release --offline --locked --manifest-path "$taps" --bin census
xz -dc "$audit/expected-census-01.json.xz" > "$out/expected-census.json"
phase census "$cache/release/census" "$out/native.txt" "$out/expected-census.json" "$out/summary.json"
phase omitted-hook-canaries bash "$audit/canary.sh" "$layout" "${out}-canaries"
phase derived-guards bash -c 'cd "$1" && sha256sum --check "$2"' _ "$layout/derived-layout" "$out/derived-before.sha256"
echo 'Arithmetic audit unit panel complete; source-level counts only, no price or benchmark advantage.'
