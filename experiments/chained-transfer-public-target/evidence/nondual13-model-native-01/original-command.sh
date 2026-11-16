#!/usr/bin/env bash
set -u
export PATH="$HOME/.cargo/bin:$PATH"
export RUSTUP_TOOLCHAIN=1.99.1
export CARGO_TARGET_DIR=/workspace/scratch/ct57-n4-unit-01-build-cache
pkg=/workspace/cryptanalysis/experiments/chained-transfer-public-target/nondual13-preflight/models
out=/workspace/scratch/ct77-nondual-model-native-01
[[ ! -e $out ]] || exit 2
mkdir "$out"
cp "$0" "$out/original-command.sh"
git rev-parse HEAD > "$out/source-head.txt"
cp "$pkg/generated/custody.json" "$out/literal-source-custody.json"
cp "$pkg/Cargo.lock" "$out/actual-Cargo.lock"
cp /workspace/scratch/ct77-nondual-model-build-03/compile.jsonl "$out/original-compile-artifacts.jsonl"
cp /workspace/scratch/ct77-nondual-model-build-03/actual-test-executable.bin "$out/original-compiled-test-executable.bin"
sha256sum "$pkg"/src/*.rs "$pkg"/generated/*.rs "$pkg/Cargo.lock" "$pkg/Cargo.toml" > "$out/frozen-source.sha256"
date -u +%FT%TZ > "$out/start.txt"
(ulimit -v 2097152; exec timeout 900 cargo test --release --offline --locked --manifest-path "$pkg/Cargo.toml" --lib -- --nocapture --test-threads=1) > "$out/native.txt" 2>&1
status=$?
printf '%s\n' "$status" > "$out/native.exit"
date -u +%FT%TZ > "$out/finish.txt"
sha256sum --check "$out/frozen-source.sha256" > "$out/final-source-guards.txt"
guard=$?
printf '%s\n' "$guard" > "$out/source-guard.exit"
if [[ $status != 0 ]]; then exit "$status"; fi
if [[ $guard != 0 ]]; then exit "$guard"; fi
grep -Eq '^test result: ok\. 1 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out;' "$out/native.txt" || exit 1
echo 'ONE comprehensive unfiltered model/torsion test passes0/sourceguards0. Matched model outcome must be read from whole native record; exit alone is not endpoint success.'
