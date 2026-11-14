#!/usr/bin/env bash
# Native development with a fresh small root and the unchanged previously compiled backends.
set -euo pipefail
out=/workspace/scratch/ct72-arithmetic-native-03
backend=/workspace/scratch/ct72-arithmetic-native-layout-03
root=/workspace/scratch/ct72-arithmetic-small-root-layout-03
solver=$root/cryptanalysis/experiments/chained-transfer-public-target/norm-assisted-ic/Cargo.toml
taps=$backend/derived-layout/n4-arithmetic-taps/Cargo.toml
export PATH=/home/agent/.cargo/bin:$PATH
export RUSTUP_TOOLCHAIN=1.99.1
export CARGO_TARGET_DIR=/workspace/scratch/ct72-arithmetic-native-01-build-cache
phase() {
 local label=$1; shift
 set +e
 "$@" > "$out/$label.txt" 2>&1
 local status=$?
 set -e
 printf '%s\n' "$status" > "$out/$label.exit"
 printf '%s %s\n' "$label" "$status" >> "$out/phases.txt"
 return "$status"
}
finish() {
 local status=$?
 trap - EXIT
 set +e
 (cd "$backend/original-layout" && sha256sum --check "$backend/original-785.sha256") > "$out/final-original-785.txt" 2>&1
 printf '%s\n' "$?" > "$out/final-original-785.exit"
 (cd "$backend/derived-layout" && sha256sum --check /workspace/scratch/ct72-arithmetic-native-01/derived-before.sha256) > "$out/final-backend-derived.txt" 2>&1
 printf '%s\n' "$?" > "$out/final-backend-derived.exit"
 (cd "$root" && sha256sum --check "$out/root-before.sha256") > "$out/final-root.txt" 2>&1
 printf '%s\n' "$?" > "$out/final-root.exit"
 printf '%s\n' "$status" > "$out/original.exit"
 date -u +%FT%TZ > "$out/finish.txt"
 exit "$status"
}
trap finish EXIT
date -u +%FT%TZ > "$out/start.txt"
rustc -Vv > "$out/rustc.txt"
(cd "$root" && find . -type f -print0 | sort -z | xargs -0 sha256sum) > "$out/root-before.sha256"
phase compile timeout 900 cargo test --release --offline --locked --manifest-path "$solver" --lib --no-run
phase native bash -c 'ulimit -v 2097152; exec timeout 900 cargo test --release --offline --locked --manifest-path "$1" --lib -- --nocapture --test-threads=1' _ "$solver"
phase ledger-unit timeout 120 cargo test --release --offline --locked --manifest-path "$taps" --lib -- --nocapture --test-threads=1
phase compare-build timeout 120 cargo build --release --offline --locked --manifest-path "$taps" --bin compare
xz -dc "$backend/original-layout/cryptanalysis/experiments/chained-transfer-public-target/ci_norm_sampling/expected-native.json.xz" > "$out/expected-native.json"
phase all86 "$CARGO_TARGET_DIR/release/compare" "$out/expected-native.json" "$out/native.txt" "$out/all-native-records.json"
