#!/usr/bin/env bash
set -u
export PATH="$HOME/.cargo/bin:$PATH"
export RUSTUP_TOOLCHAIN=1.99.1
export CARGO_TARGET_DIR=/workspace/scratch/ct57-n4-unit-01-build-cache
out=/workspace/scratch/ct77-next-edge-build-01
pkg=/workspace/cryptanalysis/experiments/chained-transfer-public-target/nondual13-next-preflight
[[ ! -e $out ]] || exit 2
mkdir "$out"
cp "$0" "$out/original-command.sh"
timeout 120 cargo generate-lockfile --offline --manifest-path "$pkg/Cargo.toml" > "$out/lock.txt" 2>&1
status=$?; printf '%s\n' "$status" > "$out/lock.exit"; [[ $status == 0 ]] || exit "$status"
cp -a "$pkg" "$out/actual-source"
timeout 120 cargo test --release --locked --offline --manifest-path "$pkg/Cargo.toml" --lib --no-run --message-format=json > "$out/compile.jsonl" 2> "$out/compile.stderr.txt"
status=$?; printf '%s\n' "$status" > "$out/compile.exit"; [[ $status == 0 ]] || exit "$status"
timeout 120 cargo build --release --locked --offline --manifest-path "$pkg/Cargo.toml" --bin next13-old-dual-control --message-format=json > "$out/control-compile.jsonl" 2> "$out/control-compile.stderr.txt"
status=$?; printf '%s\n' "$status" > "$out/control-compile.exit"; exit "$status"
