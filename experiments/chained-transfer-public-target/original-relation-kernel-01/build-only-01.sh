#!/usr/bin/env bash
set -euo pipefail
[[ $# == 3 ]] || exit 2
pkg=$(cd -- "$(dirname -- "$0")" && pwd -P)
repo=$(git -C "$pkg" rev-parse --show-toplevel)
cache=$(realpath -m "$1")
out=$(realpath -m "$2")
prior=$(realpath -m "$3")
[[ -d $cache && ! -e $out ]] || exit 2
export PATH=/home/agent/.cargo/bin:/home/agent/.elan/bin:$PATH
export RUSTUP_TOOLCHAIN=1.99.1
export CARGO_TARGET_DIR=$cache
mkdir "$out"
cd "$repo"
finish(){ local status=$?;trap - EXIT;printf '%s\n' "$status" > "$out/original.exit";date -u +%FT%TZ > "$out/finish.txt";exit "$status"; }
trap finish EXIT
date -u +%FT%TZ > "$out/start.txt"
cp "$pkg/build-only-01.sh" "$out/original-command.sh"
phase(){ local name=$1;shift;set +e;"$@" > "$out/$name.txt" 2> "$out/$name.stderr.txt";local status=$?;set -e;printf '%s\n' "$status" > "$out/$name.exit";[[ $status == 0 ]]; }
phase initial-current-inputs sha256sum --check "$pkg/frozen-current-inputs-01.sha256"
phase prior-inputs sha256sum --check "$pkg/frozen-prior-inputs-01.sha256"
phase locked-graph timeout 120 cargo generate-lockfile --offline --manifest-path "$pkg/Cargo.toml"
cp -aL "$pkg" "$out/actual-source"
phase metadata timeout 120 cargo metadata --locked --offline --format-version=1 --manifest-path "$pkg/Cargo.toml"
phase inherited-preparation python3 "$pkg/inherit_prepared.py" "$prior" "$out"
phase chain-compile timeout 120 cargo test --release --locked --offline --manifest-path "$pkg/Cargo.toml" --lib --no-run --message-format=json
python3 "$pkg/capture_binary.py" "$out" chain chained_n4_original_relation_kernel
python3 "$pkg/capture_engine.py" "$out" /workspace/crypto reused
phase auditor-compile timeout 120 cargo build --release --locked --offline --manifest-path "$pkg/Cargo.toml" --bin audit-original-relation-trace --message-format=json
python3 "$pkg/capture_binary.py" "$out" auditor audit-original-relation-trace
phase native-auditor-compile timeout 120 cargo build --release --locked --offline --manifest-path "$pkg/Cargo.toml" --bin audit-original-relation-native-records --message-format=json
python3 "$pkg/capture_binary.py" "$out" native-auditor audit-original-relation-native-records
phase final-current-inputs sha256sum --check "$pkg/frozen-current-inputs-01.sha256"
phase final-prior-inputs sha256sum --check "$pkg/frozen-prior-inputs-01.sha256"
