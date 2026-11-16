"""Freeze/copy input bytes and original native command; no Python crypto."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,shutil,subprocess
r=Path('/workspace/cryptanalysis');s=r/'experiments/chained-transfer-public-target';n=s/'gluing-models'
out=Path('/workspace/scratch/ct60-gluing-models-native-01');out.mkdir()
before=json.loads(Path('/workspace/scratch/ct59-kernel-replay-native-01/before.json').read_text());assert len(before)==2366
for line in (s/'ci_kernels/reference-01.sha256').read_text().splitlines():
    h,p=line.split('  ',1);p=(r/p).resolve();assert hashlib.sha256(p.read_bytes()).hexdigest()==h;before[str(p)]=h
p=s/'ci_kernels/reference-01.sha256';before[str(p)]=hashlib.sha256(p.read_bytes()).hexdigest()
for p in [s/'fixtures/public-five.json',s/'fixtures/expected-OUTSIDE-input.json']:
    before[str(p)]=hashlib.sha256(p.read_bytes()).hexdigest()
for p in n.rglob('*'):
    if p.is_file():before[str(p)]=hashlib.sha256(p.read_bytes()).hexdigest()
for p in [Path('/workspace/crypto/src/cryptanalysis/smith_kernel_coverage.rs'),s/'GLUING_MODELS_PROTOCOL_01.md']:
    before[str(p)]=hashlib.sha256(p.read_bytes()).hexdigest()
assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in before.items())
for name in before:
    p=Path(name);dest=out/'source'/p.relative_to('/workspace');dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,dest)
(out/'before.json').write_text(json.dumps(before,indent=2)+'\n');shutil.copyfile(__file__,out/'prepare.py');shutil.copyfile(s/'evidence/gluing-models-plan-01/primary-source-and-plan.json',out/'prospective-plan.json')
(out/'plan.json').write_text(json.dumps(dict(at=datetime.now(timezone.utc).isoformat(),prospective='27369d beforecode/all135productkernels/all6HLPmodels/actualorigins',source='actualpublished5b459ec+additivegluingmodels/fullsourceclosure',guards=len(before),scope='oneunfiltered allactualproductkernels/all6classicalmodels;900s/2GiB serial correctness;no benchmark',compiler_timeout=900,cache='reused completed P1 outside cache;not cold',source_changes='newgluingcrateonly/immutableoriginalfieldPicardNormengines'),indent=2)+'\n')
script='''#!/usr/bin/env bash
set -u
export PATH="$HOME/.cargo/bin:$HOME/.elan/bin:$PATH"
export RUSTUP_TOOLCHAIN=1.99.1
export CARGO_TARGET_DIR=/workspace/scratch/ct57-n4-unit-01-build-cache
cd /workspace/cryptanalysis
out=/workspace/scratch/ct60-gluing-models-native-01
manifest=experiments/chained-transfer-public-target/gluing-models/Cargo.toml
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
