#!/usr/bin/env bash
set -u
export PATH="$HOME/.cargo/bin:$PATH"
export RUSTUP_TOOLCHAIN=1.99.1
export CARGO_TARGET_DIR=/workspace/scratch/ct57-n4-unit-01-build-cache
pkg=/workspace/cryptanalysis/experiments/chained-transfer-public-target/norm-arithmetic-storage-02/taps
out=/workspace/scratch/ct79-observer-unit-build-02
[[ ! -e $out ]] || exit 2
mkdir "$out"
cp "$0" "$out/original-command.sh"
cp -a "$pkg" "$out/actual-source"
timeout 120 cargo test --release --locked --offline --manifest-path "$pkg/Cargo.toml" --lib --no-run --message-format=json > "$out/compile.jsonl" 2> "$out/compile.stderr.txt"
status=$?
printf '%s\n' "$status" > "$out/compile.exit"
exit "$status"
