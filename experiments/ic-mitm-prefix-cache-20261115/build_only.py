#!/usr/bin/env python3
"""One bounded default-release binary; correctness smoke, no attack timing."""
import argparse,gzip,hashlib,json,os,platform,shutil,signal,subprocess,time
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
p=argparse.ArgumentParser();p.add_argument('--source-commit',required=True);args=p.parse_args()
OUT=HERE/'build-001';OUT.mkdir(exist_ok=False)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
ids=json.loads((HERE/'identities.json').read_text())
candidate=json.loads((ROOT/'experiments/ic-bench/candidates'/(ids['0']['mitm-native']+'.json')).read_text())
hashes=candidate['implementation']['sources_sha256'];assert all(sha(ROOT/p)==d for p,d in hashes.items())
receipt={'schema':'ic-affine-preparation/v1','source_commit':args.source_commit,'source_sha256':hashes,
 'rustc':subprocess.check_output(['rustc','-Vv'],text=True),'platform':platform.platform(),
 'environment':{k:os.environ.get(k) for k in ['RUSTFLAGS','CFLAGS','CARGO_PROFILE_RELEASE_OPT_LEVEL','CARGO_PROFILE_RELEASE_CODEGEN_UNITS']},
 'purpose':'compile and manifest correctness only; no attack timing'}
try:
 argv=['cargo','build','--release','--locked','-j2','--manifest-path',str(ROOT/'suite/Cargo.toml'),'--example','ic_affine_pipeline_probe']
 process=subprocess.Popen(argv,cwd=ROOT,env=dict(os.environ,CARGO_TARGET_DIR='/tmp/ic-affine-native-target'),text=True,
  stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True)
 out=err=""
 try:out,err=process.communicate(timeout=780)
 except subprocess.TimeoutExpired:
  os.killpg(process.pid,signal.SIGKILL);out,err=process.communicate();raise TimeoutError('780-second build cap; child group terminated')
 finally:(OUT/'build.log').write_text(out+err)
 if process.returncode:raise RuntimeError('compile exit'+str(process.returncode))
 binary=OUT/'probe';shutil.copy2('/tmp/ic-affine-native-target/release/examples/ic_affine_pipeline_probe',binary)
 receipt.update(binary_sha256=sha(binary),binary_bytes=binary.stat().st_size,argv=argv,smoke=[])
 for index in [0,1]:
  r=subprocess.run([str(binary),str(HERE/'instances.json'),str(index),'manifest'],capture_output=True,text=True,timeout=30)
  (OUT/f'manifest-{index}.json').write_text(r.stdout);(OUT/f'manifest-{index}.stderr').write_text(r.stderr)
  if r.returncode:raise RuntimeError('manifest smoke exit'+str(r.returncode))
  native=json.loads(r.stdout);row=ids[str(index)]['archive']
  doc=json.loads(gzip.decompress((ROOT/'experiments/fb-archive'/row['path']).read_bytes()))
  assert [x['point'] for x in native['rows']]==doc['points']
  assert [[x['column'],x['coefficient']] for x in native['rows']]==doc['point_columns']
  receipt['smoke'].append({'index':index,'points':len(native['rows']),'columns':native['columns'],'matches_archive':True})
 receipt['native_prefix_smoke']=[]
 for index in [0,1]:
  r=subprocess.run([str(binary),str(HERE/'instances.json'),str(index),'verify-prefix'],capture_output=True,text=True,timeout=30)
  (OUT/f'prefix-smoke-{index}.json').write_text(r.stdout);(OUT/f'prefix-smoke-{index}.stderr').write_text(r.stderr)
  if r.returncode:raise RuntimeError('native x-only smoke exit'+str(r.returncode))
  check=json.loads(r.stdout);assert check['status']=='pass';receipt['native_prefix_smoke'].append(check)
 units=subprocess.run(['python3',str(HERE/'verify_frozen_units.py'),str(binary),'--out',str(OUT/'frozen-units.json')],capture_output=True,text=True,timeout=60)
 (OUT/'frozen-units.log').write_text(units.stdout+units.stderr)
 if units.returncode:raise RuntimeError('native unit receipt correctness exit'+str(units.returncode))
 receipt['frozen_units_smoke']='pass'
 receipt['status']='prepared'
except Exception as e:receipt.update(status='failed_or_capped',error=repr(e))
finally:
 (OUT/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps({'status':receipt['status']}),flush=True)
if receipt['status']!='prepared':raise SystemExit(1)
