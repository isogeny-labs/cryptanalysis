"""Freeze/copy input bytes and original native command; no Python crypto."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,shutil,subprocess
r=Path('/workspace/cryptanalysis');s=r/'experiments/chained-transfer-public-target';n=s/'two-primary'
out=Path('/workspace/scratch/ct59-two-primary-native-01');out.mkdir()
before=json.loads(Path('/workspace/crypto/research/chained_jacobian_transfers_20261110/evidence/public-n4-pcc-data-current-guard-02/current-inputs.json').read_text());assert len(before)==2191
for p in [s/'fixtures/public-five.json',s/'fixtures/expected-OUTSIDE-input.json']:
    before[str(p)]=hashlib.sha256(p.read_bytes()).hexdigest()
for p in n.rglob('*'):
    if p.is_file():before[str(p)]=hashlib.sha256(p.read_bytes()).hexdigest()
assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in before.items())
for name in before:
    p=Path(name);dest=out/'source'/p.relative_to('/workspace');dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,dest)
(out/'before.json').write_text(json.dumps(before,indent=2)+'\n');shutil.copyfile(__file__,out/'prepare.py');shutil.copyfile(s/'evidence/two-primary-plan-01/plan.json',out/'prospective-plan.json')
(out/'plan.json').write_text(json.dumps(dict(at=datetime.now(timezone.utc).isoformat(),prospective='c3b30d before code/actual2Sylowfourkernelhypotheses',source='68d P1 unchanged plus additiveV2',guards=len(before),scope='oneunfiltered actualcofactorgroup4 scout;900s/2GiB serial correctness;no benchmark',compiler_timeout=900,cache='reused completed P1 outside cache;not cold',source_changes='newscout only/immutableoriginalfieldPicardNormengines'),indent=2)+'\n')
script='''#!/usr/bin/env bash
set -u
export PATH="$HOME/.cargo/bin:$HOME/.elan/bin:$PATH"
export RUSTUP_TOOLCHAIN=1.99.1
export CARGO_TARGET_DIR=/workspace/scratch/ct57-n4-unit-01-build-cache
cd /workspace/cryptanalysis
out=/workspace/scratch/ct59-two-primary-native-01
manifest=experiments/chained-transfer-public-target/two-primary/Cargo.toml
date -u +%Y-%m-%dT%H:%M:%SZ > "$out/start.txt"
rustc -Vv > "$out/rustc.txt" 2>&1
timeout 900 cargo test --release --offline --locked --manifest-path "$manifest" --lib --no-run > "$out/compile.log" 2>&1
build=$?
printf '%s\\n' "$build" > "$out/compile.exit"
if [ "$build" -eq 0 ]; then
  (ulimit -v 2097152; timeout 900 cargo test --release --offline --locked --manifest-path "$manifest" --lib -- --nocapture --test-threads=1) > "$out/native.log" 2>&1
  status=$?
else
  status=$build
  cp "$out/compile.log" "$out/native.log"
fi
printf '%s\\n' "$status" > "$out/native.exit"
date -u +%Y-%m-%dT%H:%M:%SZ > "$out/finish.txt"
python3 - "$out" <<'GUARD'
from pathlib import Path
import hashlib,json,sys
o=Path(sys.argv[1]);before=json.loads((o/'before.json').read_text());after={p:hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in before};changed=[p for p in before if before[p]!=after[p]]
(o/'after.json').write_text(json.dumps(after,indent=2)+'\\n');(o/'guards.json').write_text(json.dumps(dict(count=len(before),changed=changed),indent=2)+'\\n');raise SystemExit(bool(changed))
GUARD
guard=$?
printf '%s\\n' "$guard" > "$out/guard.exit"
if [ "$status" -ne 0 ]; then exit "$status"; fi
exit "$guard"
'''
launcher=Path(str(out)+'.sh');launcher.write_text(script);shutil.copyfile(launcher,out/'original-command.sh')
print(str(launcher),len(before),flush=True)
