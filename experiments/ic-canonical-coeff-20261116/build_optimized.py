#!/usr/bin/env python3
"""One bounded default-release binary; correctness smoke, no attack timing."""
import argparse,gzip,hashlib,json,os,platform,shutil,signal,subprocess,time
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
p=argparse.ArgumentParser();p.add_argument('--source-commit',required=True);args=p.parse_args()
OUT=HERE/'build-optimized-001';OUT.mkdir(exist_ok=False)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
from source_manifest import hashes as source_hashes
# Reconstruct the exact admitted baseline suite, then overlay only the changed file.
# Main has unrelated dependency changes; these are outside this controlled comparison.
import tarfile
FROZEN=Path('/tmp/ic-canonical-frozen-source-001');FROZEN.mkdir(exist_ok=False)
archive_path=Path('/jobs/20261117-020802-ae70/src.tar.gz')
assert sha(archive_path)==json.loads((HERE/'baseline-source.json').read_text())['sha256']
with tarfile.open(archive_path,'r:gz') as archive:
 for member in archive.getmembers():
  archive.extract(member,FROZEN,filter='data')
overlay='suite/src/cryptanalysis/ic_boundary/batched_walk.rs'
(FROZEN/overlay).write_bytes((ROOT/overlay).read_bytes())
from source_manifest import sources
hashes={p:sha(FROZEN/p) for p in sources}
ROOT=FROZEN
receipt={'schema':'ic-affine-preparation/v1','source_commit':args.source_commit,'source_sha256':hashes,
 'rustc':subprocess.check_output(['rustc','-Vv'],text=True),'platform':platform.platform(),
 'environment':{k:os.environ.get(k) for k in ['RUSTFLAGS','CFLAGS','CARGO_PROFILE_RELEASE_OPT_LEVEL','CARGO_PROFILE_RELEASE_CODEGEN_UNITS']},
 'purpose':'compile and manifest correctness only; no attack timing'}
try:
 import tarfile
 with tarfile.open(Path('/jobs')/'20261117-020802-ae70'/'shards/0/out.tar.gz','r:gz') as archive:
  old_bytes=archive.extractfile('experiments/ic-inverse-regression-20261116/build-optimized-001/receipt.json').read()
  assert hashlib.sha256(old_bytes).hexdigest()==json.loads((HERE/'baseline-input.json').read_text())['receipt_sha256']
  old_receipt=json.loads(old_bytes)
 assert receipt['rustc']==old_receipt['rustc'] and receipt['environment']==old_receipt['environment'], 'compiler/environment differs from frozen current control'
 receipt['matched_compiler_control']='pass'
 assert [p for p in hashes if hashes[p]!=old_receipt['source_sha256'][p]]==['suite/src/cryptanalysis/ic_boundary/batched_walk.rs']
 receipt['controlled_source']={'baseline_job':'20261117-020802-ae70','baseline_archive_sha256':sha(archive_path),'overlay':overlay,'source_delta':'only batched_walk.rs','main_dependency_changes_excluded':True}
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
 for index in range(5):
  r=subprocess.run([str(binary),str(HERE/'instances.json'),str(index),'manifest'],capture_output=True,text=True,timeout=30)
  (OUT/f'manifest-{index}.json').write_text(r.stdout);(OUT/f'manifest-{index}.stderr').write_text(r.stderr)
  if r.returncode:raise RuntimeError('manifest smoke exit'+str(r.returncode))
  native=json.loads(r.stdout);n=json.loads((HERE/'instances.json').read_text())[index]['field']['degree'];row=json.loads((HERE/f'archive-n{n}.json').read_text())
  doc=json.loads(gzip.decompress((ROOT/'experiments/fb-archive'/row['path']).read_bytes()))
  assert [x['point'] for x in native['rows']]==doc['points']
  assert [[x['column'],x['coefficient']] for x in native['rows']]==doc['point_columns']
  receipt['smoke'].append({'index':index,'points':len(native['rows']),'columns':native['columns'],'matches_archive':True})
 receipt['native_table_smoke']=[]
 for index in range(5):
  r=subprocess.run([str(binary),str(HERE/'instances.json'),str(index),'verify-table'],capture_output=True,text=True,timeout=30)
  (OUT/f'table-smoke-{index}.json').write_text(r.stdout);(OUT/f'table-smoke-{index}.stderr').write_text(r.stderr)
  if r.returncode:raise RuntimeError('native x-only smoke exit'+str(r.returncode))
  check=json.loads(r.stdout);assert check['status']=='pass' and check['vector_pairs']>0 and check['complete_map_comparisons']==35
  assert check['vector_backend'] in ['avx2-pclmul128','avx2-vpclmul']
  assert check['vector_pclmul128_pairs']==(check['vector_pairs'] if check['vector_backend']=='avx2-pclmul128' else 2*check['vector_const_pairs'])
  assert check['vector_packed_square_pairs']>0 and check['vector_pairs']==4*check['vector_packed_square_pairs'] and check['vector_const_pairs']==check['vector_packed_square_pairs']
  receipt['native_table_smoke'].append(check)
 units=subprocess.run(['python3',str(HERE/'verify_frozen_units.py'),str(binary),'--out',str(OUT/'frozen-units.json')],capture_output=True,text=True,timeout=60)
 (OUT/'frozen-units.log').write_text(units.stdout+units.stderr)
 if units.returncode:raise RuntimeError('native unit receipt correctness exit'+str(units.returncode))
 receipt['frozen_units_smoke']='pass'
 receipt['walk_smoke']=[]
 for index in range(5):
  r=subprocess.run([str(binary),str(HERE/'instances.json'),str(index),'verify-walkbatch','0'],capture_output=True,text=True,timeout=30)
  (OUT/f'walk-smoke-{index}.json').write_text(r.stdout);(OUT/f'walk-smoke-{index}.stderr').write_text(r.stderr)
  if r.returncode:raise RuntimeError('walker smoke exit'+str(r.returncode))
  check=json.loads(r.stdout)
  assert check['status']=='pass' and check['checks']==512 and check['complete_stream_comparisons']==4 and check['has_clmul']
  assert check['native_counters']['walk_batch_native_backend']==1 and check['scalar_counters']['walk_batch_native_backend']==0
  assert check['native_counters']['walk_batch_pair_adds']>0
  assert check['vector_counters']['walk_batch_vector_pairs']>0 and check['vector_counters']['walk_batch_vector_backend']==1
  assert check['inverse_vector_counters']['walk_batch_inverse_vector_backend']==1 and check['inverse_vector_counters']['walk_batch_inverse_vector_elements']>0
  receipt['walk_smoke'].append({k:v for k,v in check.items() if k!='frames'})
 unit_argv=['cargo','test','--locked','-j2','--manifest-path',str(ROOT/'suite/Cargo.toml'),'--lib','batched_walk','--','--nocapture']
 unit_process=subprocess.Popen(unit_argv,cwd=ROOT,env=dict(os.environ,CARGO_TARGET_DIR='/tmp/ic-affine-native-target'),text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True)
 try:unit_out,unit_err=unit_process.communicate(timeout=180)
 except subprocess.TimeoutExpired:
  os.killpg(unit_process.pid,signal.SIGKILL);unit_out,unit_err=unit_process.communicate();raise TimeoutError('native walker unit180s cap')
 finally:(OUT/'walker-unit.log').write_text((locals().get('unit_out') or '')+(locals().get('unit_err') or ''))
 assert unit_process.returncode==0 and '6 passed; 0 failed' in unit_out
 receipt['native_walker_unit']='pass';receipt['native_walker_unit_argv']=unit_argv
 vector_argv=['cargo','test','--locked','-j2','--manifest-path',str(ROOT/'suite/Cargo.toml'),'--lib','vector_full','--','--nocapture']
 vector_process=subprocess.Popen(vector_argv,cwd=ROOT,env=dict(os.environ,CARGO_TARGET_DIR='/tmp/ic-affine-native-target'),text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True)
 vector_out=vector_err=''
 try:vector_out,vector_err=vector_process.communicate(timeout=60)
 except subprocess.TimeoutExpired:
  os.killpg(vector_process.pid,signal.SIGKILL);vector_out,vector_err=vector_process.communicate();raise TimeoutError('native vector formula unit60s cap')
 finally:(OUT/'vector-full-unit.log').write_text(vector_out+vector_err)
 assert vector_process.returncode==0 and '2 passed; 0 failed' in vector_out and 'AVX2 full-point vector formulas accepted' in vector_err and 'skipped:' not in vector_err
 receipt['native_vector_full_unit']='pass';receipt['native_vector_full_unit_argv']=vector_argv
 const_argv=['cargo','test','--locked','-j2','--manifest-path',str(ROOT/'suite/Cargo.toml'),'--lib','const_cached_reduction','--','--nocapture']
 const_process=subprocess.run(const_argv,cwd=ROOT,env=dict(os.environ,CARGO_TARGET_DIR='/tmp/ic-affine-native-target'),text=True,capture_output=True,timeout=60)
 (OUT/'const-unit.log').write_text(const_process.stdout+const_process.stderr)
 assert const_process.returncode==0 and '1 passed; 0 failed' in const_process.stdout
 receipt['native_const_unit']='pass';receipt['native_const_unit_argv']=const_argv
 framework_argv=['cargo','test','--locked','-j2','--manifest-path',str(ROOT/'suite/Cargo.toml'),'--lib','ic_framework','--','--nocapture']
 framework_process=subprocess.run(framework_argv,cwd=ROOT,env=dict(os.environ,CARGO_TARGET_DIR='/tmp/ic-affine-native-target'),text=True,capture_output=True,timeout=90)
 (OUT/'framework-unit.log').write_text(framework_process.stdout+framework_process.stderr)
 assert framework_process.returncode==0 and '27 passed; 0 failed' in framework_process.stdout
 receipt['native_framework_unit']='pass';receipt['native_framework_unit_argv']=framework_argv
 inverse_argv=['cargo','test','--locked','-j2','--manifest-path',str(ROOT/'suite/Cargo.toml'),'--lib','vector_inverse','--','--nocapture']
 inverse_process=subprocess.run(inverse_argv,cwd=ROOT,env=dict(os.environ,CARGO_TARGET_DIR='/tmp/ic-affine-native-target'),text=True,capture_output=True,timeout=90)
 (OUT/'vector-inverse-unit.log').write_text(inverse_process.stdout+inverse_process.stderr)
 assert inverse_process.returncode==0 and '3 passed; 0 failed' in inverse_process.stdout and 'SIMD inverse products accepted' in inverse_process.stderr and 'skipped:' not in inverse_process.stderr
 receipt['native_vector_inverse_unit']='pass';receipt['native_vector_inverse_unit_argv']=inverse_argv
 receipt['status']='prepared'
except Exception as e:receipt.update(status='failed_or_capped',error=repr(e))
finally:
 (OUT/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps({'status':receipt['status']}),flush=True)
if receipt['status']!='prepared':raise SystemExit(1)
