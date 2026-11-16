#!/usr/bin/env bash
set -u
export PATH="$HOME/.cargo/bin:$PATH"
export RUSTUP_TOOLCHAIN=1.99.1
export CARGO_TARGET_DIR=/workspace/scratch/ct57-n4-unit-01-build-cache
out=/workspace/scratch/ct75-norm-arithmetic-parity-01
manifest=/workspace/scratch/ct75-norm-arithmetic-layout-01/derived-layout/cryptanalysis/experiments/chained-transfer-public-target/norm-halving-evaluator/Cargo.toml
original=/workspace/scratch/ct75-norm-arithmetic-layout-01/original-layout/cryptanalysis/experiments/chained-transfer-public-target/norm-halving-evaluator/Cargo.lock
cargo metadata --offline --format-version 1 --manifest-path "$manifest" > "$out/metadata.json" 2> "$out/metadata.stderr.txt"
status=$?
printf '%s\n' "$status" > "$out/metadata.exit"
if [[ $status != 0 ]]; then exit "$status"; fi
awk 'BEGIN { RS="\n\\[\\[package\\]\\]\n" } /source = / { print }' "$original" > "$out/original-registry-blocks.txt"
awk 'BEGIN { RS="\n\\[\\[package\\]\\]\n" } /source = / { print }' "$(dirname "$manifest")/Cargo.lock" > "$out/derived-registry-blocks.txt"
cmp "$out/original-registry-blocks.txt" "$out/derived-registry-blocks.txt" > "$out/registry-compare.txt" 2>&1
status=$?
printf '%s\n' "$status" > "$out/registry-compare.exit"
if [[ $status != 0 ]]; then exit "$status"; fi
timeout 900 cargo test --release --offline --locked --manifest-path "$manifest" --lib --no-run > "$out/compile.txt" 2>&1
status=$?
printf '%s\n' "$status" > "$out/compile.exit"
if [[ $status == 0 ]]; then
 (ulimit -v 2097152; exec timeout 900 env N4_ARITHMETIC_OBSERVER=disabled cargo test --release --offline --locked --manifest-path "$manifest" --lib -- --nocapture --test-threads=1) > "$out/native.txt" 2>&1
 status=$?
 printf '%s\n' "$status" > "$out/native.exit"
 if [[ $status == 0 ]]; then
  /workspace/scratch/ct74-norm-halving-audit-02/audit_native.bin --compare /workspace/scratch/ct74-norm-halving-audit-02/expected-native-05.json "$out/native.txt" "$out/all-four-whole-records.json" > "$out/compare.txt" 2>&1
  status=$?
  printf '%s\n' "$status" > "$out/compare.exit"
 fi
fi
exit "$status"
