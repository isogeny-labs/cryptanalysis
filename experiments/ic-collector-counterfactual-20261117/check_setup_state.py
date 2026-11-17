#!/usr/bin/env python3
"""Bounded local admission; preserve prior receipts and every failed log."""
import argparse,hashlib,json,os,platform,signal,subprocess,time
from pathlib import Path
from source_manifest import sources,changed_sources
P=Path(__file__).resolve().parent;ROOT=P.parents[1]
F=Path('/tmp/ic-canonical-frozen-source-001')
assert F.resolve()==ROOT/'experiments/ic-static-witness-map-20261117/local-frozen-source-stash'
old=json.loads((P/'baseline-source-hashes.json').read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert all(sha(F/n)==old[n] for n in sources if n not in changed_sources)
ap=argparse.ArgumentParser();ap.add_argument('--attempt',required=True);a=ap.parse_args();assert a.attempt.isdigit()
O=P/('local-tmp/setup-state-'+a.attempt);O.mkdir(exist_ok=False)
for n in changed_sources:
 p=F/n;t=p.with_name(p.name+'.setup-state');t.write_bytes((ROOT/n).read_bytes());os.replace(t,p)
hashes={n:sha(F/n) for n in sources}
assert {n for n in sources if hashes[n]!=old[n]}==set(changed_sources)
env=dict(os.environ,TMPDIR=str(P/'local-tmp'),CARGO_TARGET_DIR=str(ROOT/'suite/target'),CARGO_INCREMENTAL='0')
common=['--locked','-j2','--manifest-path',str(F/'suite/Cargo.toml')]
commands=[['cargo','test',*common,'--lib','counterfactual','--','--nocapture'],['cargo','test',*common,'--lib','ic_framework','--','--nocapture'],['cargo','clippy',*common,'--lib','--example','ic_affine_pipeline_probe','--','-D','warnings'],['cargo','build',*common,'--example','ic_affine_pipeline_probe']]
r=dict(status='started',purpose='ARM correctness only; native indexed execution and timing unmeasured',platform=platform.platform(),source_sha256=hashes,checks=[])
try:
 for i,argv in enumerate(commands):
  assert {n:sha(F/n) for n in sources}==hashes
  log=O/f'check-{i}.log';start=time.time()
  with log.open('w') as out:
   proc=subprocess.Popen(argv,env=env,cwd=ROOT,stdout=out,stderr=subprocess.STDOUT,start_new_session=True)
   try:code=proc.wait(timeout=240)
   except subprocess.TimeoutExpired:os.killpg(proc.pid,signal.SIGKILL);proc.wait();code=124
  r['checks'].append(dict(argv=argv,exit_code=code,seconds=time.time()-start,log=str(log.relative_to(P)),sha256=sha(log)))
  assert code==0,log
 r['status']='pass'
except Exception as e:r.update(status='failed_or_capped',error=repr(e));raise
finally:(O/'receipt.json').write_text(json.dumps(r,indent=2)+'\n')
print(json.dumps(dict(status=r['status'],checks=len(r['checks']))))
