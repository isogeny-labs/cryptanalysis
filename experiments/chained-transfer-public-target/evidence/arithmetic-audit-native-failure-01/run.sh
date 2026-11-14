#!/usr/bin/env bash
# Bounded unit development only; no benchmark or operation price.
set -uo pipefail
out=/workspace/scratch/ct72-arithmetic-native-01
layout=/workspace/scratch/ct72-arithmetic-native-layout-03
study=$layout/derived-layout/cryptanalysis/experiments/chained-transfer-public-target
export PATH=/home/agent/.cargo/bin:$PATH
export RUSTUP_TOOLCHAIN=1.99.1
export CARGO_TARGET_DIR=/workspace/scratch/ct72-arithmetic-native-01-build-cache
mkdir "$CARGO_TARGET_DIR" || exit 2
rustc -Vv > "$out/rustc.txt"
date -u +%FT%TZ > "$out/start.txt"
phase() {
 local label=$1; shift
 "$@" > "$out/$label.txt" 2>&1
 local status=$?
 printf '%s\n' "$status" > "$out/$label.exit"
 printf '%s %s\n' "$label" "$status" >> "$out/phases.txt"
 return "$status"
}
finish() {
 local status=$?
 trap - EXIT
 (cd "$layout/original-layout" && sha256sum --check "$layout/original-785.sha256") > "$out/final-original-785.txt" 2>&1
 printf '%s\n' "$?" > "$out/final-original-785.exit"
 date -u +%FT%TZ > "$out/finish.txt"
 printf '%s\n' "$status" > "$out/original.exit"
 exit "$status"
}
trap finish EXIT
set -e
phase lock-solver cargo generate-lockfile --offline --manifest-path "$study/norm-assisted-ic/Cargo.toml"
phase lock-taps cargo generate-lockfile --offline --manifest-path "$layout/derived-layout/n4-arithmetic-taps/Cargo.toml"
(cd "$layout/derived-layout" && find . -type f -print0 | sort -z | xargs -0 sha256sum) > "$out/derived-before.sha256"
phase compile timeout 900 cargo test --release --offline --locked --manifest-path "$study/norm-assisted-ic/Cargo.toml" --lib --no-run
phase native bash -c 'ulimit -v 2097152; exec timeout 900 cargo test --release --offline --locked --manifest-path "$1" --lib -- --nocapture --test-threads=1' _ "$study/norm-assisted-ic/Cargo.toml"
phase ledger-unit timeout 120 cargo test --release --offline --locked --manifest-path "$layout/derived-layout/n4-arithmetic-taps/Cargo.toml" --lib -- --nocapture --test-threads=1
phase compare-build timeout 120 cargo build --release --offline --locked --manifest-path "$layout/derived-layout/n4-arithmetic-taps/Cargo.toml" --bin compare
xz -dc "$layout/original-layout/cryptanalysis/experiments/chained-transfer-public-target/ci_norm_sampling/expected-native.json.xz" > "$out/expected-native.json"
phase all86 "$CARGO_TARGET_DIR/release/compare" "$out/expected-native.json" "$out/native.txt" "$out/all-native-records.json"
phase derived-guards bash -c 'cd "$1" && sha256sum --check "$2"' _ "$layout/derived-layout" "$out/derived-before.sha256"
