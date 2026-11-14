#!/usr/bin/env bash
set -u
export PATH="$HOME/.cargo/bin:$HOME/.elan/bin:$PATH"
export RUSTUP_TOOLCHAIN=1.99.1
export CARGO_TARGET_DIR=/workspace/scratch/ct57-n4-unit-01-build-cache
cd /workspace/cryptanalysis
out=/workspace/scratch/ct60-gluing-maps-native-03
manifest=experiments/chained-transfer-public-target/gluing-maps/Cargo.toml
date -u +%Y-%m-%dT%H:%M:%SZ > "$out/start.txt"
rustc -Vv > "$out/rustc.txt" 2>&1
timeout 900 cargo test --release --offline --locked --manifest-path "$manifest" --lib --no-run > "$out/compile.log" 2>&1
build=$?
printf '%s\n' "$build" > "$out/compile.exit"
if [ "$build" -eq 0 ]; then
  (ulimit -v 2097152; timeout 900 cargo test --release --offline --locked --manifest-path "$manifest" --lib -- --nocapture --test-threads=1) > "$out/native.log" 2>&1
  status=$?
else
  status=$build
  cp "$out/compile.log" "$out/native.log"
fi
printf '%s\n' "$status" > "$out/native.exit"
date -u +%Y-%m-%dT%H:%M:%SZ > "$out/finish.txt"
python3 - "$out" <<'GUARD'
from pathlib import Path
import hashlib,json,sys
o=Path(sys.argv[1]);before=json.loads((o/'before.json').read_text());after={p:hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in before};changed=[p for p in before if before[p]!=after[p]]
(o/'after.json').write_text(json.dumps(after,indent=2)+'\n');(o/'guards.json').write_text(json.dumps(dict(count=len(before),changed=changed),indent=2)+'\n');raise SystemExit(bool(changed))
GUARD
guard=$?
printf '%s\n' "$guard" > "$out/guard.exit"
if [ "$status" -ne 0 ]; then exit "$status"; fi
exit "$guard"
