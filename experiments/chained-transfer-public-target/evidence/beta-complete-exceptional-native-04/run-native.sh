#!/usr/bin/env bash
set -u
export PATH="$HOME/.cargo/bin:$PATH"
export RUSTUP_TOOLCHAIN=1.99.1
export CARGO_TARGET_DIR=/workspace/scratch/ct57-n4-unit-01-build-cache
cd /workspace/cryptanalysis
out=/workspace/scratch/ct73-beta-complete-native-04
cp "$CARGO_TARGET_DIR/release/deps/chained_n4_beta_complete_evaluator-659d0ab084b703d4" "$out/actual-test-executable.bin"
date -u +%FT%TZ > "$out/start.txt"
(ulimit -v 2097152; timeout 900 cargo test --release --offline --locked --manifest-path experiments/chained-transfer-public-target/beta-complete-evaluator/Cargo.toml --lib -- --nocapture --test-threads=1) > "$out/native.txt" 2>&1
status=$?
printf '%s\n' "$status" > "$out/native.exit"
date -u +%FT%TZ > "$out/finish.txt"
python3 - "$out" <<'PY'
from pathlib import Path
import hashlib,json,sys
p=Path(sys.argv[1]);before=json.loads((p/'before.json').read_text());after={x:hashlib.sha256(Path(x).read_bytes()).hexdigest()for x in before};changed=[x for x in before if before[x]!=after[x]];(p/'after.json').write_text(json.dumps(after,indent=2)+'\n');(p/'guards.json').write_text(json.dumps(dict(count=len(before),changed=changed),indent=2)+'\n');raise SystemExit(bool(changed))
PY
guard=$?
printf '%s\n' "$guard" > "$out/guard.exit"
if [ "$status" -ne 0 ]; then exit "$status"; fi
exit "$guard"
