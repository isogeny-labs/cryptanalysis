#!/usr/bin/env bash
set -u
export PATH="$HOME/.cargo/bin:$PATH"
export RUSTUP_TOOLCHAIN=1.99.1
export CARGO_TARGET_DIR=/workspace/scratch/ct57-n4-unit-01-build-cache
out=/workspace/scratch/ct75-norm-arithmetic-controls-01
manifest=/workspace/scratch/ct75-norm-arithmetic-layout-01/derived-layout/norm-census/Cargo.toml
cargo generate-lockfile --offline --manifest-path "$manifest" > "$out/lock.txt" 2>&1
status=$?
printf '%s\n' "$status" > "$out/lock.exit"
if [[ $status != 0 ]]; then exit "$status"; fi
timeout 900 cargo build --release --offline --locked --manifest-path "$manifest" > "$out/compile.txt" 2>&1
status=$?
printf '%s\n' "$status" > "$out/compile.exit"
if [[ $status == 0 ]]; then
 cp "$CARGO_TARGET_DIR/release/norm-halving-arithmetic-census" "$out/actual-census-executable.bin"
 (ulimit -v 2097152; exec timeout 120 env N4_ARITHMETIC_OBSERVER=enabled "$CARGO_TARGET_DIR/release/norm-halving-arithmetic-census" --controls) > "$out/native.txt" 2>&1
 status=$?
 printf '%s\n' "$status" > "$out/native.exit"
fi
exit "$status"
