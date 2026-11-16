#!/usr/bin/env bash
set -u
export PATH="$HOME/.elan/bin:$HOME/.cargo/bin:$PATH"
export ELAN_TOOLCHAIN=leanprover/lean4:v4.35.0
cd /workspace/cryptanalysis
out=/workspace/scratch/ct63-odd-product-lean-producer-01
date -u +%Y-%m-%dT%H:%M:%SZ > "$out/start.txt"
lean --version > "$out/lean-version.txt" 2>&1
set +e
timeout 900 bash /workspace/crypto/tools/lean/proof-gate.sh --out "$out/proofs" experiments/chained-transfer-public-target/odd-product-maps/lean/OddProductChain.lean > "$out/native.log" 2>&1
status=$?
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
