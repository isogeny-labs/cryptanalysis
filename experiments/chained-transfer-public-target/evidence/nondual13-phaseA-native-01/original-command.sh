#!/usr/bin/env bash
set -u
export PATH="$HOME/.cargo/bin:$PATH"
export RUSTUP_TOOLCHAIN=1.99.1
export CARGO_TARGET_DIR=/workspace/scratch/ct57-n4-unit-01-build-cache
study=/workspace/cryptanalysis/experiments/chained-transfer-public-target
out=/workspace/scratch/ct76-nondual13-native-01
[[ ! -e $out ]] || exit 2
mkdir "$out"
cp "$0" "$out/original-command.sh"
git rev-parse HEAD > "$out/source-head.txt"
cp "$study/nondual13-preflight/generated/custody.json" "$out/literal-prefix-custody.json"
cp "$study/nondual13-preflight/src/append.rs" "$out/actual-append.rs"
cp "$study/nondual13-preflight/Cargo.lock" "$out/actual-Cargo.lock"
cp /workspace/scratch/ct76-nondual13-build-01/compile02.jsonl "$out/original-build-artifacts.jsonl"
cp /workspace/scratch/ct76-nondual13-build-01/actual-binary02.json "$out/original-build-binary.json"
sha256sum "$study/nondual13-preflight/src/append.rs" "$study/nondual13-preflight/generated/lib.rs" "$study/nondual13-preflight/Cargo.lock" > "$out/frozen-source.sha256"
date -u +%FT%TZ > "$out/positive.start"
(ulimit -v 2097152; exec timeout 900 cargo test --release --offline --locked --manifest-path "$study/nondual13-preflight/Cargo.toml" --lib -- --nocapture --test-threads=1) > "$out/positive-native.txt" 2>&1
status=$?
printf '%s\n' "$status" > "$out/positive-native.exit"
date -u +%FT%TZ > "$out/positive.finish"
[[ $status == 0 ]] || exit "$status"
grep -Eq '^test result: ok\. 1 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out;' "$out/positive-native.txt" || exit 1
cp /workspace/scratch/ct76-nondual13-build-01/actual-preflight-test-executable-02.bin "$out/actual-positive-executable.bin"
date -u +%FT%TZ > "$out/negative.start"
(ulimit -v 2097152; exec timeout 900 cargo run --release --offline --locked --manifest-path "$study/nondual13-preflight/Cargo.toml" --bin nondual13-old-dual-control) > "$out/negative-native.txt" 2>&1
status=$?
printf '%s\n' "$status" > "$out/negative-native.exit"
date -u +%FT%TZ > "$out/negative.finish"
[[ $status == 101 ]] || exit 1
grep -F '"accepted_nondual":false' "$out/negative-native.txt" >/dev/null || exit 1
grep -F '"actual_gcd_degree":168' "$out/negative-native.txt" >/dev/null || exit 1
grep -F 'old dual must fail actual nondual kernel acceptance' "$out/negative-native.txt" >/dev/null || exit 1
cp "$CARGO_TARGET_DIR/release/nondual13-old-dual-control" "$out/actual-negative-executable.bin"
sha256sum --check "$out/frozen-source.sha256" > "$out/final-source-guards.txt" || exit 1
printf '0\n' > "$out/original.exit"
echo 'ONE unfiltered actual elliptic phaseA passes0; old dual actual kernel gate rejects101 with168gcd; source guards0. Full product/model phaseB still open.'
