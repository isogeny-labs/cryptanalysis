#!/usr/bin/env bash
set -u
export PATH="$HOME/.cargo/bin:$PATH"
export RUSTUP_TOOLCHAIN=1.99.1
export CARGO_TARGET_DIR=/workspace/scratch/ct57-n4-unit-01-build-cache
out=/workspace/scratch/ct75-norm-arithmetic-fixture-01
manifest=/workspace/scratch/ct75-norm-arithmetic-layout-01/original-layout/norm-fixture/Cargo.toml
python3 - <<'PYGUARD'
from pathlib import Path
import json,hashlib
p=Path('/workspace/scratch/ct75-norm-arithmetic-fixture-01');deps=Path('/workspace/scratch/ct57-n4-unit-01-build-cache/release/deps');(p/'dependency-cache-before.json').write_text(json.dumps({str(q):{'bytes':q.stat().st_size,'sha256':hashlib.sha256(q.read_bytes()).hexdigest()}for q in deps.iterdir()if q.is_file()and q.suffix in {'.rlib','.rmeta','.o'}},indent=2)+'\n')
PYGUARD
cargo generate-lockfile --offline --manifest-path "$manifest" > "$out/lock.txt" 2>&1
status=$?
printf '%s\n' "$status" > "$out/lock.exit"
if [[ $status != 0 ]]; then exit "$status"; fi
timeout 900 cargo build --release --offline --locked --manifest-path "$manifest" > "$out/compile.txt" 2>&1
status=$?
printf '%s\n' "$status" > "$out/compile.exit"
if [[ $status == 0 ]]; then
 cp "$CARGO_TARGET_DIR/release/norm-halving-arithmetic-fixture" "$out/actual-fixture-executable.bin"
 xz -dc /workspace/cryptanalysis/docs/research-artifacts/chained-transfer/norm-halving-01/expected-native-05.json.xz > "$out/whole-native-golden.json"
 (ulimit -v 2097152; exec timeout 900 "$CARGO_TARGET_DIR/release/norm-halving-arithmetic-fixture" "$out/whole-native-golden.json" "$out/cases60.json") > "$out/native.txt" 2>&1
 status=$?
 printf '%s\n' "$status" > "$out/native.exit"
fi
exit "$status"
