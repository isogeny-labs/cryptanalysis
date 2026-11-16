#!/usr/bin/env bash
set -u
export PATH="$HOME/.cargo/bin:$PATH"
export RUSTUP_TOOLCHAIN=1.99.1
export CARGO_TARGET_DIR=/workspace/scratch/ct57-n4-unit-01-build-cache
cd /workspace/cryptanalysis
out=/workspace/scratch/ct74-strong-baseline-native-02
date -u +%FT%TZ > "$out/start.txt"
rustc -Vv > "$out/rustc.txt"
timeout 900 cargo test --release --offline --locked --manifest-path experiments/chained-transfer-public-target/norm-halving-evaluator/Cargo.toml --lib --no-run > "$out/compile.txt" 2>&1
status=$?
printf '%s\n' "$status" > "$out/compile.exit"
if [ "$status" -eq 0 ]; then
  (ulimit -v 2097152; exec timeout 900 cargo test --release --offline --locked --manifest-path experiments/chained-transfer-public-target/norm-halving-evaluator/Cargo.toml --lib -- --nocapture --test-threads=1) > "$out/native.txt" 2>&1
  status=$?
  printf '%s\n' "$status" > "$out/native.exit"
fi
date -u +%FT%TZ > "$out/finish.txt"
python3 /workspace/scratch/ct74_baseline_guard_and_binary_02.py
guard=$?
if [ "$status" -ne 0 ]; then exit "$status"; fi
exit "$guard"
