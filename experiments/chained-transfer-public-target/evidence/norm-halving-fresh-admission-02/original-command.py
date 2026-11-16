"""Published Git-file materialization, admission controls, source/binary custody."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,os,re,shutil,subprocess,sys
r=Path('/workspace/cryptanalysis');source=sys.argv[1];producer='3d49af7f3d0a28e76b79e4825c9d2324e85853d2';study='experiments/chained-transfer-public-target';s=r/study
assert subprocess.check_output(['git','rev-parse',source],cwd=r,text=True).strip()==source
layout=Path('/workspace/scratch/ct74-norm-halving-replay-layout-02');layout.mkdir();reference=s/'ci_norm_halving/reference-01.sha256';refs=[x.split('  ',1)[1]for x in reference.read_text().splitlines()];assert len(refs)==929
for name,repo,commit,files in[
 ('cryptanalysis',r,source,[p for p in refs if not p.startswith('../crypto/')]+[study+'/ci_norm_halving/reference-01.sha256']),
 ('crypto',Path('/workspace/crypto'),producer,[p.removeprefix('../crypto/')for p in refs if p.startswith('../crypto/')])]:
 path=layout/name;q=subprocess.run(['git','worktree','add','--detach','--no-checkout',str(path),commit],cwd=repo,capture_output=True);(layout/(name+'-create.txt')).write_bytes(q.stdout+q.stderr);assert q.returncode==0
 subprocess.run(['git','sparse-checkout','init','--no-cone'],cwd=path,check=True);subprocess.run(['git','sparse-checkout','set','--no-cone','--stdin'],cwd=path,input=('\n'.join('/'+x for x in sorted(set(files)))+'\n').encode(),check=True);subprocess.run(['git','read-tree','-mu','HEAD'],cwd=path,check=True)
 assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=path,text=True).strip()==commit
 status=subprocess.check_output(['git','status','--porcelain','--untracked-files=all'],cwd=path);(layout/(name+'-status.txt')).write_bytes(status);assert not status
c=layout/'cryptanalysis';up=layout/'crypto';cs=c/study;out=Path('/workspace/scratch/ct74-norm-halving-full-02');out.mkdir();driver=Path('/workspace/scratch/ct74-norm-halving-driver-02');assert not driver.exists()and not Path(str(driver)+'-build-cache').exists()
rel=study+'/evidence/odd-product-maps-acceptance-02/all-native-records.json.xz';fixture=c/rel;entry=json.loads((fixture.parent/'.artifacts.json').read_text())['files'][fixture.name];assert entry==dict(bytes=120752,sha256='f5c45a14d9f3496a7136c2976f5a741901e15641047a988fcce0b6ad1e8ca5f4');raw=(r/rel).read_bytes();assert len(raw)==entry['bytes']and hashlib.sha256(raw).hexdigest()==entry['sha256'];shutil.copyfile(r/rel,fixture);fixture.chmod(0o444)
q=subprocess.run(['python3','tools/artifacts/artifacts.py','verify',rel],cwd=c,capture_output=True);(out/'original-fixture-verify.txt').write_bytes(q.stdout+q.stderr);(out/'original-fixture-verify.exit').write_text(str(q.returncode)+'\n');assert q.returncode==0
(out/'fixture-materialization.json').write_text(json.dumps(dict(path=rel,entry=entry,method='read-only copy of already genuine original; original local verification0, no claimed new remote read',origin='43505654954/22d22eb0e/768f4a/0bb0f5'),indent=2)+'\n')
docsrel='docs/research-artifacts/chained-transfer/norm-halving-01'
entries=json.loads((c/docsrel/'.artifacts.json').read_text())['files']
for name,row in entries.items():
 src=r/docsrel/name;dest=c/docsrel/name;raw=src.read_bytes();assert len(raw)==row['bytes']and hashlib.sha256(raw).hexdigest()==row['sha256'];shutil.copyfile(src,dest);dest.chmod(0o444)
q=subprocess.run(['python3','tools/artifacts/artifacts.py','verify',docsrel],cwd=c,capture_output=True);(out/'norm-halving-original-fixture-verify.txt').write_bytes(q.stdout+q.stderr);(out/'norm-halving-original-fixture-verify.exit').write_text(str(q.returncode)+'\n');assert q.returncode==0
(out/'norm-halving-fixture-materialization.json').write_text(json.dumps({'directory':docsrel,'entries':entries,'method':'readonly local copy of original genuine43599404964/6444d7f50 objects; originalverify0; not a new remote read','transparent_PDF_alias':'report.pdf corresponds to original whole-report-PDF.bin with exactsamebytes'},indent=2)+'\n')
before={}
for line in reference.read_text().splitlines():
 h,p=line.split('  ',1);path=c/p;assert hashlib.sha256(path.read_bytes()).hexdigest()==h,p;before[str(path)]=h
localref=cs/'ci_norm_halving/reference-01.sha256';before[str(localref)]=hashlib.sha256(localref.read_bytes()).hexdigest();assert len(before)==930
(out/'before.json').write_text(json.dumps(before,indent=2)+'\n');shutil.copyfile(localref,out/'original-reference.sha256');shutil.copyfile(__file__,out/'prepare.py')
env=dict(os.environ,PATH='/home/agent/.cargo/bin:/home/agent/.elan/bin:'+os.environ['PATH'],RUSTUP_TOOLCHAIN='1.99.1',ELAN_TOOLCHAIN='leanprover/lean4:v4.35.0');ad=out/'admission';ad.mkdir();results=[]
def reject(name,dest,environment=env):
 q=subprocess.run(['bash',str(cs/'ci_norm_halving/check.sh'),str(up),str(dest)],cwd=c,env=environment,capture_output=True,timeout=60);(ad/(name+'.txt')).write_bytes(q.stdout+q.stderr);(ad/(name+'.exit')).write_text(str(q.returncode)+'\n');results.append(dict(name=name,actual_exit=q.returncode,output_created=dest.exists()));(ad/'results.json').write_text(json.dumps(results,indent=2)+'\n');assert q.returncode==2 and not dest.exists()
missing=env.copy();missing['PATH']='/usr/bin:/bin';reject('missing-tool',out/'missing-tool-output',missing)
try:
 q=subprocess.run(['git','checkout','--detach','a719f6f75f67576ce3835d8acc6e47bb25a3cbe4'],cwd=up,capture_output=True);(ad/'wrong-head-checkout.txt').write_bytes(q.stdout+q.stderr);assert q.returncode==0;reject('wrong-producer-head',out/'wrong-head-output')
finally:
 q=subprocess.run(['git','checkout','--detach',producer],cwd=up,capture_output=True);(ad/'restore-producer-head.txt').write_bytes(q.stdout+q.stderr);assert q.returncode==0
reject('output-in-source',cs/'should-not-exist')
dest=out/'occupied-cache-output';cache=Path(str(dest)+'-build-cache');cache.mkdir()
try:reject('existing-cache',dest)
finally:cache.rmdir()
assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in before.items());(ad/'restoration.json').write_text(json.dumps(dict(all930_inputs_unchanged=True,all_four_original_exit2_no_output=True,producer_restored=producer),indent=2)+'\n')
(out/'plan.json').write_text(json.dumps(dict(at=datetime.now(timezone.utc).isoformat(),consumer=source,producer=producer,protocols='6dc948 andNORM_HALVING_REPLAY_PROTOCOL_01; source5ac59843 published beforefull',source_inputs=929,source_plus_manifest=930,driver_output=str(driver),derived_cache=str(driver)+'-build-cache',cache_scope='fresh target outside BOTH captured output roots; ordinary registry shared, not benchmark',timeout_s=2400,phases='21ordered:19zero/twoactual101;everytee0',acceptance='native4/all4wholeJSON/no masks/two unchanged original10gates/ninebindings/all finalguards',admissions=results,scope='bounded correctness development/independent fresh source replay; no performance measurement'),indent=2)+'\n')
launcher=Path('/workspace/scratch/ct74-norm-halving-full-02.sh');launcher.write_text('''#!/usr/bin/env bash
set -u
export PATH="$HOME/.cargo/bin:$HOME/.elan/bin:$PATH"
export RUSTUP_TOOLCHAIN=1.99.1
export ELAN_TOOLCHAIN=leanprover/lean4:v4.35.0
cd /workspace/scratch/ct74-norm-halving-replay-layout-02/cryptanalysis
out=/workspace/scratch/ct74-norm-halving-full-02
date -u +%FT%TZ > "$out/start.txt"
timeout 2400 bash experiments/chained-transfer-public-target/ci_norm_halving/check.sh ../crypto /workspace/scratch/ct74-norm-halving-driver-02 > "$out/native.txt" 2>&1
status=$?
printf '%s\\n' "$status" > "$out/native.exit"
date -u +%FT%TZ > "$out/finish.txt"
python3 - "$out" <<'GUARDS'
from pathlib import Path
import hashlib,json,re,shutil,sys
o=Path(sys.argv[1]);d=Path('/workspace/scratch/ct74-norm-halving-driver-02');before=json.loads((o/'before.json').read_text());after={p:hashlib.sha256(Path(p).read_bytes()).hexdigest()for p in before};changed=[p for p in before if before[p]!=after[p]];(o/'after.json').write_text(json.dumps(after,indent=2)+'\\n');(o/'guards.json').write_text(json.dumps(dict(count=len(before),changed=changed),indent=2)+'\\n')
receipt={'derived_cache_outside_captured_roots':str(d)+'-build-cache','actual_executable_paths':[]}
compile_text=(d/'compile.txt').read_text()if(d/'compile.txt').exists()else'';native_text=(d/'native.txt').read_text()if(d/'native.txt').exists()else''
a=re.search(r'Executable unittests src/lib.rs \\(([^\\n]+)\\)',compile_text);b=re.search(r'Running unittests src/lib.rs \\(([^\\n]+)\\)',native_text)
if a and b:
 assert a[1]==b[1];p=Path(a[1]);dest=o/'actual-test-executable.bin';shutil.copyfile(p,dest);receipt['actual_executable_paths'].append(dict(kind='unit',path=str(p),copied=str(dest),sha256=hashlib.sha256(dest.read_bytes()).hexdigest()))
 for name in['audit_native','halving_identity']:
  p=Path(str(d)+'-build-cache')/'release'/name
  if p.is_file():
   dest=o/(name+'-executable.bin');shutil.copyfile(p,dest);receipt['actual_executable_paths'].append(dict(kind=name,path=str(p),copied=str(dest),sha256=hashlib.sha256(dest.read_bytes()).hexdigest()))
(o/'binary-custody.json').write_text(json.dumps(receipt,indent=2)+'\\n')
if(o/'native.exit').read_text().strip()=='0':assert len(receipt['actual_executable_paths'])==3
raise SystemExit(bool(changed))
GUARDS
guard=$?
printf '%s\\n' "$guard" > "$out/guard.exit"
if [ "$status" -ne 0 ]; then exit "$status"; fi
exit "$guard"
''');shutil.copyfile(launcher,out/'original-command.sh');print(json.dumps(dict(source=source,layout=str(layout),guards=930,admissions=results,launcher=str(launcher),driver=str(driver))),flush=True)
