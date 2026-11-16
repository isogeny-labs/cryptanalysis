#!/usr/bin/env python3
"""Bounded release preparation and input smoke checks, no attack measurement."""
import argparse
import gzip
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import signal
import subprocess
import time

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
parser=argparse.ArgumentParser();parser.add_argument('--source-commit',required=True);args=parser.parse_args()
OUT=HERE/'build-001';OUT.mkdir(exist_ok=False);start=time.monotonic()


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def command(argv,limit):
 remaining=1700-(time.monotonic()-start)
 if remaining<=0:raise TimeoutError('preparation controller cap')
 p=subprocess.Popen(argv,cwd=ROOT,env=dict(os.environ,CARGO_TARGET_DIR='/tmp/ic-s3-pipeline-prepared'),
                    stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,start_new_session=True)
 try:out,err=p.communicate(timeout=min(limit,remaining))
 except subprocess.TimeoutExpired:
  os.killpg(p.pid,signal.SIGKILL);out,err=p.communicate();return 124,out,err+'\nprocess group killed at cap\n'
 return p.returncode,out,err


ids=json.loads((HERE/'identities.json').read_text())
reference=json.loads((ROOT/'experiments/ic-bench/candidates'/(ids['0']['buchberger-f2']['reference']+'.json')).read_text())
source_hashes=reference['implementation']['sources_sha256']
assert all(sha(ROOT/p)==digest for p,digest in source_hashes.items())
receipt={'schema':'ic-s3-preparation/v1','source_commit':args.source_commit,'source_sha256':source_hashes,
         'rustc':subprocess.check_output(['rustc','-Vv'],text=True),'platform':platform.platform(),
         'cpuinfo':Path('/proc/cpuinfo').read_text(),'environment':{k:os.environ.get(k) for k in ['RUSTFLAGS','CFLAGS','CARGO_PROFILE_RELEASE_OPT_LEVEL','CARGO_PROFILE_RELEASE_CODEGEN_UNITS']},
         'binaries':{},'purpose':'binary preparation and manifest-mode correctness; no attack timing'}
try:
 for variant in ['reference','direct']:
  argv=['cargo','build','--release','--locked','-j2','--manifest-path',str(ROOT/'suite/Cargo.toml'),'--example','ic_s3_pipeline_probe']
  if variant=='direct':argv+=['--features','s3-direct-coefficients']
  code,out,err=command(argv,780);(OUT/f'{variant}-build.log').write_text(out+err)
  if code:raise RuntimeError(f'{variant} build exit{code}')
  binary=OUT/('probe-'+variant);shutil.copy2('/tmp/ic-s3-pipeline-prepared/release/examples/ic_s3_pipeline_probe',binary)
  ldd=subprocess.run(['ldd',str(binary)],capture_output=True,text=True)
  receipt['binaries'][variant]={'sha256':sha(binary),'bytes':binary.stat().st_size,'argv':argv,'ldd':ldd.stdout+ldd.stderr,'manifest_smoke':[]}
  for index,n in enumerate([15,18]):
   code,out,err=command([str(binary),str(HERE/'instances.json'),str(index),'manifest'],30)
   (OUT/f'{variant}-manifest-n{n}.json').write_text(out);(OUT/f'{variant}-manifest-n{n}.stderr').write_text(err)
   if code:raise RuntimeError(f'{variant} manifest n{n} exit{code}')
   native=json.loads(out);archive=json.loads((HERE/f'archive-n{n}.json').read_text())
   doc=json.loads(gzip.decompress((ROOT/'experiments/fb-archive'/archive['path']).read_bytes()))
   assert [r['point'] for r in native['rows']]==doc['points']
   assert [[r['column'],r['coefficient']] for r in native['rows']]==doc['point_columns']
   receipt['binaries'][variant]['manifest_smoke'].append({'n':n,'points':len(native['rows']),'columns':native['columns'],'matches_archive':True})
 receipt['status']='prepared'
except Exception as e:receipt.update(status='failed_or_capped',error=repr(e))
finally:
 (OUT/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps({'status':receipt['status'],'binaries':list(receipt['binaries'])}),flush=True)
if receipt['status']!='prepared':raise SystemExit(1)
