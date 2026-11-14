"""Exact Git worktrees and admission/source custody only; invokes original tools."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, os, shutil, subprocess

r=Path('/workspace/cryptanalysis'); s=r/'experiments/chained-transfer-public-target'
source='fb9ee1d613eebcd3459c02007b9bce06da218b47'; producer='3d49af7f3d0a28e76b79e4825c9d2324e85853d2'
layout=Path('/workspace/scratch/ct67-odd-product-refinement-replay-layout-01'); layout.mkdir()
reference=s/'ci_odd_refinement/reference-01.sha256'
refs=[line.split('  ',1)[1] for line in reference.read_text().splitlines()]
assert len(refs)==702
for name,repo,commit,files in [
    ('cryptanalysis',r,source,[p for p in refs if not p.startswith('../crypto/')]+['experiments/chained-transfer-public-target/ci_odd_refinement/reference-01.sha256']),
    ('crypto',Path('/workspace/crypto'),producer,[p.removeprefix('../crypto/') for p in refs if p.startswith('../crypto/')])]:
    path=layout/name
    p=subprocess.run(['git','worktree','add','--detach','--no-checkout',str(path),commit],cwd=repo,capture_output=True)
    (layout/(name+'-create.log')).write_bytes(p.stdout+p.stderr);assert p.returncode==0
    subprocess.run(['git','sparse-checkout','init','--no-cone'],cwd=path,check=True)
    subprocess.run(['git','sparse-checkout','set','--no-cone','--stdin'],cwd=path,input=('\n'.join('/'+p for p in sorted(set(files)))+'\n').encode(),check=True)
    subprocess.run(['git','read-tree','-mu','HEAD'],cwd=path,check=True)
    assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=path,text=True).strip()==commit
    status=subprocess.check_output(['git','status','--porcelain','--untracked-files=all'],cwd=path)
    (layout/(name+'-status.txt')).write_bytes(status); assert not status
c=layout/'cryptanalysis';up=layout/'crypto';cs=c/'experiments/chained-transfer-public-target'
out=Path('/workspace/scratch/ct67-odd-product-refinement-full-01');out.mkdir()
fixture_relative='experiments/chained-transfer-public-target/evidence/odd-product-maps-acceptance-02/all-native-records.json.xz'
fixture=c/fixture_relative
entry=json.loads((fixture.parent/'.artifacts.json').read_text())['files'][fixture.name]
assert entry==dict(bytes=120752,sha256='f5c45a14d9f3496a7136c2976f5a741901e15641047a988fcce0b6ad1e8ca5f4')
original=r/fixture_relative;raw=original.read_bytes();assert len(raw)==entry['bytes']and hashlib.sha256(raw).hexdigest()==entry['sha256']
shutil.copyfile(original,fixture)
materialized=subprocess.run(['python3','tools/artifacts/artifacts.py','verify',fixture_relative],cwd=c,capture_output=True)
(out/'original-fixture-verify.log').write_bytes(materialized.stdout+materialized.stderr);(out/'original-fixture-verify.exit').write_text(str(materialized.returncode)+'\n');assert materialized.returncode==0
(out/'fixture-materialization.json').write_text(json.dumps(dict(path=fixture_relative,entry=entry,method='read-only copy of already genuine physical original,not a new remote read;original tool local verification0',genuine='43505654954/22d22eb0e/768f4a/0bb0f5',CI='new workflow separately performs original pinned remote hydration'),indent=2)+'\n')
assert not subprocess.check_output(['git','status','--porcelain','--untracked-files=all'],cwd=c)

before={}
for line in reference.read_text().splitlines():
    h,p=line.split('  ',1); path=(c/p).resolve();assert hashlib.sha256(path.read_bytes()).hexdigest()==h
    before[str(path)]=h
localref=cs/'ci_odd_refinement/reference-01.sha256';before[str(localref)]=hashlib.sha256(localref.read_bytes()).hexdigest()
assert len(before)==703
(out/'before.json').write_text(json.dumps(before,indent=2)+'\n')
shutil.copyfile(__file__,out/'prepare.py')
shutil.copyfile(localref,out/'original-reference.sha256')
(out/'plan.json').write_text(json.dumps(dict(at=datetime.now(timezone.utc).isoformat(),source=source,producer=producer,
    plan='7705d9/d3de82/3d6caf published before admission/full',portable_inputs=702,outer_guards=703,
    timeout_s=2100,build_cache=str(out)+'-build-cache',phase_pairs='10positive0/0',
    original_native_and_Lean='actual transported kernels/all135/all9/independent rank;identical source images all3/33oddzero/public5/ALL7wholeJSON/bothoriginal3auditedgates/3exactbindings',scope='routine bounded local correctness/CI development,not experiment or benchmark'),indent=2)+'\n')
env=os.environ.copy();env['PATH']=str(Path.home()/'.cargo/bin')+':'+str(Path.home()/'.elan/bin')+':'+env['PATH']
env['RUSTUP_TOOLCHAIN']='1.99.1';env['ELAN_TOOLCHAIN']='leanprover/lean4:v4.35.0';env['CARGO_TARGET_DIR']=str(out)+'-build-cache'
ad=out/'admission';ad.mkdir();results=[]
def test(name,dest,environment=env):
    p=subprocess.run(['bash',str(cs/'ci_odd_refinement/check.sh'),str(up),str(dest)],cwd=c,env=environment,capture_output=True,timeout=60)
    (ad/(name+'.log')).write_bytes(p.stdout+p.stderr);(ad/(name+'.exit')).write_text(str(p.returncode)+'\n')
    results.append(dict(name=name,original_exit=p.returncode,output_created=dest.exists()))
    (ad/'results.json').write_text(json.dumps(results,indent=2)+'\n')
    assert p.returncode==2 and not dest.exists(),results[-1]
missing=env.copy();missing['PATH']='/usr/bin:/bin';test('missing-tool',out/'missing-tool-output',missing)
try:
    p=subprocess.run(['git','checkout','--detach','a719f6f75f70276ce3835d8acc6e47bb25a3cbe4'],cwd=up,capture_output=True)
    (ad/'wrong-head-checkout.log').write_bytes(p.stdout+p.stderr);assert p.returncode==0
    test('wrong-head',out/'wrong-head-output')
finally:
    p=subprocess.run(['git','checkout','--detach',producer],cwd=up,capture_output=True)
    (ad/'restore-head.log').write_bytes(p.stdout+p.stderr);assert p.returncode==0
p=cs/'PROOF_MAP.md';old=p.read_bytes()
try:
    p.write_bytes(old+b'\nDirty admission control.\n');test('dirty-source',out/'dirty-source-output')
finally:p.write_bytes(old)
test('output-in-source',cs/'admission-should-not-exist')
assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in before.items())
assert not subprocess.check_output(['git','status','--porcelain'],cwd=c)
assert not subprocess.check_output(['git','status','--porcelain'],cwd=up)
(ad/'restoration.json').write_text(json.dumps(dict(all703_unchanged=True,clean_siblings=True,four_exit2_no_output=True),indent=2)+'\n')
launcher=Path('/workspace/scratch/ct67-odd-product-refinement-full-01.sh')
launcher.write_text('''#!/usr/bin/env bash
set -u
export PATH="$HOME/.cargo/bin:$HOME/.elan/bin:$PATH"
export RUSTUP_TOOLCHAIN=1.99.1
export ELAN_TOOLCHAIN=leanprover/lean4:v4.35.0
export CARGO_TARGET_DIR=/workspace/scratch/ct67-odd-product-refinement-full-01-build-cache
cd /workspace/scratch/ct67-odd-product-refinement-replay-layout-01/cryptanalysis
out=/workspace/scratch/ct67-odd-product-refinement-full-01
date -u +%Y-%m-%dT%H:%M:%SZ > "$out/start.txt"
timeout 2100 bash experiments/chained-transfer-public-target/ci_odd_refinement/check.sh ../crypto "$out/driver" > "$out/native.log" 2>&1
status=$?
printf '%s\\n' "$status" > "$out/native.exit"
date -u +%Y-%m-%dT%H:%M:%SZ > "$out/finish.txt"
python3 - "$out" <<'GUARDS'
from pathlib import Path
import hashlib,json,sys
o=Path(sys.argv[1]);before=json.loads((o/'before.json').read_text());after={p:hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in before};changed=[p for p in before if before[p]!=after[p]]
(o/'after.json').write_text(json.dumps(after,indent=2)+'\\n');(o/'guards.json').write_text(json.dumps(dict(count=len(before),changed=changed),indent=2)+'\\n');raise SystemExit(bool(changed))
GUARDS
guard=$?
printf '%s\\n' "$guard" > "$out/guard.exit"
if [ "$status" -ne 0 ]; then exit "$status"; fi
exit "$guard"
''')
shutil.copyfile(launcher,out/'original-command.sh')
print(json.dumps(dict(layout=str(layout),source=source,admissions=results,outer_guards=703,launcher=str(launcher))),flush=True)
