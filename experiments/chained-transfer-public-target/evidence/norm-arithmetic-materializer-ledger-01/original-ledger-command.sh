#!/usr/bin/env bash
set -u
export PATH="$HOME/.cargo/bin:$PATH"
export RUSTUP_TOOLCHAIN=1.99.1
export CARGO_TARGET_DIR=/workspace/scratch/ct57-n4-unit-01-build-cache
out=/workspace/scratch/ct75-norm-arithmetic-ledger-01
(ulimit -v 2097152; exec timeout 120 cargo test --release --offline --locked --manifest-path /workspace/scratch/ct75-norm-arithmetic-layout-01/derived-layout/n4-arithmetic-taps/Cargo.toml --lib -- --nocapture --test-threads=1) > "$out/native.txt" 2>&1
status=$?
printf '%s\n' "$status" > "$out/native.exit"
exit "$status"
