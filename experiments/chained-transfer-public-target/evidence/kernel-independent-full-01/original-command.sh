#!/usr/bin/env bash
set -u
export PATH="$HOME/.cargo/bin:$HOME/.elan/bin:$PATH"
export RUSTUP_TOOLCHAIN=1.99.1
export ELAN_TOOLCHAIN=leanprover/lean4:v4.35.0
export CARGO_TARGET_DIR=/workspace/scratch/ct60-kernel-full-01-build-cache
cd /workspace/scratch/ct60-kernel-replay-layout-01/cryptanalysis
out=/workspace/scratch/ct60-kernel-full-01
date -u +%Y-%m-%dT%H:%M:%SZ > "$out/start.txt"
timeout 2100 bash experiments/chained-transfer-public-target/ci_kernels/check.sh ../crypto "$out/driver" > "$out/native.log" 2>&1
status=$?
printf '%s\n' "$status" > "$out/native.exit"
date -u +%Y-%m-%dT%H:%M:%SZ > "$out/finish.txt"
python3 - "$out" <<'GUARDS'
from pathlib import Path
import hashlib,json,sys
o=Path(sys.argv[1]);before=json.loads((o/'before.json').read_text());after={p:hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in before};changed=[p for p in before if before[p]!=after[p]]
(o/'after.json').write_text(json.dumps(after,indent=2)+'\n');(o/'guards.json').write_text(json.dumps(dict(count=len(before),changed=changed),indent=2)+'\n');raise SystemExit(bool(changed))
GUARDS
guard=$?
printf '%s\n' "$guard" > "$out/guard.exit"
if [ "$status" -ne 0 ]; then exit "$status"; fi
exit "$guard"
