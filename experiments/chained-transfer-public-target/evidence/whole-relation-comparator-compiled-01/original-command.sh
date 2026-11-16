#!/usr/bin/env bash
# Thin local finite-correctness build; no field-engine preparation or timings claim.
set -euo pipefail
repo=/workspace/cryptanalysis
pkg=$repo/experiments/chained-transfer-public-target/ci_original_relation/audit
out=/workspace/scratch/ct107-whole-relation-comparator-build-02
[[ ! -e $out ]] || exit 2
mkdir "$out"
cp "$0" "$out/original-command.sh"
cp -a "$pkg" "$out/actual-source"
export PATH=/home/agent/.cargo/bin:$PATH RUSTUP_TOOLCHAIN=1.99.1
export CARGO_TARGET_DIR=/dev/shm/ct107-whole-relation-comparator-target
cd "$repo"
trap 'status=$?;printf "%s\n" "$status" > "$out/original.exit";date -u +%FT%TZ > "$out/finish.txt"' EXIT
date -u +%FT%TZ > "$out/start.txt"
phase(){ local label=$1;shift;set +e;"$@" > "$out/$label.txt" 2> "$out/$label.stderr.txt";local code=$?;set -e;printf '%s\n' "$code" > "$out/$label.exit";printf '%s %s\n' "$label" "$code";[[ $code == 0 ]]; }
phase prior1532 sha256sum --check experiments/chained-transfer-public-target/original-relation-character-01/frozen-prior-inputs-01.sha256
phase rustfmt rustfmt --edition 2021 --config skip_children=true --check "$pkg/src/lib.rs" "$pkg/src/main.rs"
phase metadata timeout 120 cargo metadata --locked --offline --format-version=1 --manifest-path "$pkg/Cargo.toml"
phase release-build timeout 120 cargo build --release --locked --offline --manifest-path "$pkg/Cargo.toml" --message-format=json
phase release-library-tests timeout 120 cargo test --release --locked --offline --manifest-path "$pkg/Cargo.toml" --lib
cp "$CARGO_TARGET_DIR/release/audit-original-relation-historical" "$out/actual-compiled-auditor.bin"
sha256sum "$CARGO_TARGET_DIR/release/audit-original-relation-historical" "$out/actual-compiled-auditor.bin" > "$out/whole-binary-sha256.txt"
phase final-source cmp "$pkg/src/lib.rs" "$out/actual-source/src/lib.rs"
