#!/usr/bin/env bash
set -u
export PATH="$HOME/.cargo/bin:$PATH"
export RUSTUP_TOOLCHAIN=1.99.1
export CARGO_TARGET_DIR=/workspace/scratch/ct57-n4-unit-01-build-cache
study=/workspace/cryptanalysis/experiments/chained-transfer-public-target
pkg="$study/nondual13-next-preflight"
out=/workspace/scratch/ct77-next-native-01
[[ ! -e $out ]] || exit 2
mkdir "$out"
cp "$0" "$out/original-command.sh"
git rev-parse HEAD > "$out/source-head.txt"
[[ $(cat "$out/source-head.txt") == f0167e430befd4304b170689e8caebcbdabbc6ad ]] || exit 2
[[ -z $(git status --porcelain) ]] || exit 2
bash scripts/checkpoint.sh gate > "$out/original-immediate-gate.txt" 2>&1
status=$?;printf '%s\n' "$status" > "$out/original-immediate-gate.exit";[[ $status == 0 ]] || exit "$status"
sha256sum "$pkg"/src/*.rs "$pkg"/src/bin/*.rs "$pkg"/generated/*.rs "$pkg"/Cargo.toml "$pkg"/Cargo.lock "$pkg"/models/src/*.rs "$pkg"/models/generated/*.rs "$pkg"/models/Cargo.toml "$pkg"/models/Cargo.lock > "$out/frozen-source.sha256"
sha256sum --check "$pkg/frozen-prior-inputs-01.sha256" > "$out/prior-source-guards.txt"
status=$?;printf '%s\n' "$status" > "$out/prior-source-guards.exit";[[ $status == 0 ]] || exit "$status"
sha256sum --check "$study/ci_norm_halving/reference-01.sha256" > "$out/original929-source-guards.txt"
status=$?;printf '%s\n' "$status" > "$out/original929-source-guards.exit";[[ $status == 0 ]] || exit "$status"
for phase in edge model; do
  mkdir "$out/$phase"
  build="/workspace/scratch/ct77-next-$phase-build-01"
  cp "$build/compile.jsonl" "$out/$phase/original-compile.jsonl"
  cp "$build/actual-test-executable.bin" "$out/$phase/original-compiled-test-executable.bin"
done
date -u +%FT%TZ > "$out/edge/start.txt"
(ulimit -v 2097152; exec timeout 900 cargo test --release --locked --offline --manifest-path "$pkg/Cargo.toml" --lib -- --nocapture --test-threads=1) > "$out/edge/native.txt" 2>&1
status=$?;printf '%s\n' "$status" > "$out/edge/native.exit";date -u +%FT%TZ > "$out/edge/finish.txt";[[ $status == 0 ]] || exit "$status"
grep -Eq '^test result: ok\. 1 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out;' "$out/edge/native.txt" || exit 1
(ulimit -v 2097152; exec timeout 900 /workspace/scratch/ct77-next-edge-build-01/actual-control-executable.bin) > "$out/edge/actual-old-dual-control.txt" 2>&1
status=$?;printf '%s\n' "$status" > "$out/edge/actual-old-dual-control.exit";[[ $status == 101 ]] || exit 1
grep -Fq 'old second dual must fail next nondual kernel acceptance' "$out/edge/actual-old-dual-control.txt" || exit 1
bash scripts/checkpoint.sh gate > "$out/model/original-immediate-gate.txt" 2>&1
status=$?;printf '%s\n' "$status" > "$out/model/original-immediate-gate.exit";[[ $status == 0 ]] || exit "$status"
date -u +%FT%TZ > "$out/model/start.txt"
(ulimit -v 2097152; exec timeout 900 cargo test --release --locked --offline --manifest-path "$pkg/models/Cargo.toml" --lib -- --nocapture --test-threads=1) > "$out/model/native.txt" 2>&1
status=$?;printf '%s\n' "$status" > "$out/model/native.exit";date -u +%FT%TZ > "$out/model/finish.txt";[[ $status == 0 ]] || exit "$status"
grep -Eq '^test result: ok\. 1 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out;' "$out/model/native.txt" || exit 1
sha256sum --check "$out/frozen-source.sha256" > "$out/final-source-guards.txt"
status=$?;printf '%s\n' "$status" > "$out/final-source-guards.exit";exit "$status"
