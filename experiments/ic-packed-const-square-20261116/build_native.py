#!/usr/bin/env python3
"""One bounded native preparation, authoritative revision from job metadata."""
import hashlib,json,os,platform,shutil,signal,subprocess,tarfile,gzip
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
OUT=HERE/'build-001';OUT.mkdir(exist_ok=False)
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
from source_manifest import sources,changed_sources
binding=json.loads((HERE/'baseline-input.json').read_text())
with tarfile.open(Path('/jobs')/binding['source_job']/'shards/0/out.tar.gz','r:gz') as archive:
 rb=archive.extractfile('experiments/ic-compact-pair-table-20261116/build-001/receipt.json').read()
 assert hashlib.sha256(rb).hexdigest()==binding['receipt_sha256'];old_receipt=json.loads(rb);assert old_receipt['status']=='prepared'
 assert old_receipt['source_commit']==binding['receipt_source_commit']
metadata_bytes=(Path('/jobs')/os.environ['JOB_ID']/'job.json').read_bytes();metadata=json.loads(metadata_bytes)
assert not metadata['git']['dirty'] and metadata['gpu']=='L4' and metadata['cpu']==4 and metadata['memory_gib']==8
baseline_archive=Path('/jobs/20261117-020802-ae70/src.tar.gz')
assert sha(baseline_archive)=='7d50769b5aa850c68cfa64deeb90f5ebd633f2fa7713c48ed13aaa4783caedce'
control_manifest=Path(old_receipt['argv'][old_receipt['argv'].index('--manifest-path')+1]);assert control_manifest==Path('/tmp/ic-canonical-frozen-source-001/suite/Cargo.toml')
FROZEN=control_manifest.parents[1];FROZEN.mkdir(exist_ok=False)
with tarfile.open(baseline_archive,'r:gz') as archive:archive.extractall(FROZEN,filter='data')
coefficient_archive=Path('/jobs/20261117-033328-8366/src.tar.gz')
assert sha(coefficient_archive)=='bc4a04c1dd2f65196eab714dbfa02fa4ed4a9526ea53303e1f2da5e759297715'
with tarfile.open(coefficient_archive,'r:gz') as archive:
 name='suite/src/cryptanalysis/ic_boundary/batched_walk.rs';data=archive.extractfile(name).read();assert hashlib.sha256(data).hexdigest()==old_receipt['source_sha256'][name];(FROZEN/name).write_bytes(data)
compact_archive=Path('/jobs')/binding['source_job']/'src.tar.gz';assert sha(compact_archive)==binding['snapshot_sha256']
with tarfile.open(compact_archive,'r:gz') as archive:
 for name in ['suite/src/cryptanalysis/ic_boundary.rs','suite/src/cryptanalysis/ic_framework/batch_mitm.rs','suite/examples/ic_affine_pipeline_probe.rs']:
  data=archive.extractfile(name).read();assert hashlib.sha256(data).hexdigest()==old_receipt['source_sha256'][name];(FROZEN/name).write_bytes(data)
assert {p:sha(FROZEN/p) for p in sources}==old_receipt['source_sha256']
for name in changed_sources:(FROZEN/name).write_bytes((ROOT/name).read_bytes())
hashes={p:sha(FROZEN/p) for p in sources};assert {p for p in sources if hashes[p]!=old_receipt['source_sha256'][p]}==set(changed_sources)
ROOT=FROZEN
receipt={'schema':'ic-affine-preparation/v1','status':'started','source_commit':metadata['git']['commit'],'source_sha256':hashes,
 'rustc':subprocess.check_output(['rustc','-Vv'],text=True),'platform':platform.platform(),
 'environment':{k:os.environ.get(k) for k in ['RUSTFLAGS','CFLAGS','CARGO_PROFILE_RELEASE_OPT_LEVEL','CARGO_PROFILE_RELEASE_CODEGEN_UNITS']},
 'purpose':'compile and correctness only; no attack timing',
 'controlled_source':{'baseline_job':binding['source_job'],'baseline_receipt_sha256':binding['receipt_sha256'],'original_archive_sha256':sha(baseline_archive),'coefficient_archive_sha256':sha(coefficient_archive),'compact_archive_sha256':sha(compact_archive),'changed_sources':changed_sources,'actual_source_revision_from_job_metadata':True}}
try:
 assert receipt['rustc']==old_receipt['rustc'] and receipt['environment']==old_receipt['environment'],'compiler/environment mismatch'
 receipt['matched_compiler_control']='pass'
 argv=['cargo','build','--release','--locked','-j2','--manifest-path',str(ROOT/'suite/Cargo.toml'),'--example','ic_affine_pipeline_probe']
 with (OUT/'build.log').open('w') as log:
  process=subprocess.Popen(argv,cwd=ROOT,env=dict(os.environ,CARGO_TARGET_DIR='/tmp/ic-affine-native-target'),text=True,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
  try:process.wait(timeout=780)
  except subprocess.TimeoutExpired:
   os.killpg(process.pid,signal.SIGKILL);process.wait();raise TimeoutError('780-second build cap; child group terminated')
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
  assert check['compact_map_comparisons']==5 and check['compact_entry_payload_bytes']==8
  assert check['vector_backend'] in ['avx2-pclmul128','avx2-vpclmul']
  assert check['vector_pclmul128_pairs']==(check['vector_pairs'] if check['vector_backend']=='avx2-pclmul128' else 2*check['vector_const_pairs'])
  assert check['vector_packed_square_pairs']>0 and check['vector_pairs']==2*check['vector_packed_square_pairs'] and 2*check['vector_const_pairs']==check['vector_packed_square_pairs'] and check['vector_const_packed_square_pairs']==check['vector_const_pairs']>0
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
 compact_argv=['cargo','test','--locked','-j2','--manifest-path',str(ROOT/'suite/Cargo.toml'),'--lib','compact_pair_witness','--','--nocapture']
 compact=subprocess.run(compact_argv,cwd=ROOT,env=dict(os.environ,CARGO_TARGET_DIR='/tmp/ic-affine-native-target'),capture_output=True,text=True,timeout=90)
 (OUT/'compact-unit.log').write_text(compact.stdout+compact.stderr)
 assert compact.returncode==0 and '3 passed; 0 failed' in compact.stdout
 receipt['native_compact_unit']='pass';receipt['native_compact_unit_argv']=compact_argv
 packed_argv=['cargo','test','--locked','-j2','--manifest-path',str(ROOT/'suite/Cargo.toml'),'--lib','packed_const_square','--','--nocapture']
 packed=subprocess.run(packed_argv,cwd=ROOT,env=dict(os.environ,CARGO_TARGET_DIR='/tmp/ic-affine-native-target'),capture_output=True,text=True,timeout=90)
 (OUT/'packed-const-unit.log').write_text(packed.stdout+packed.stderr)
 assert packed.returncode==0 and '1 passed; 0 failed' in packed.stdout and 'SIMD packed constant squares accepted' in packed.stderr and 'skipped:' not in packed.stderr
 receipt['native_packed_const_unit']='pass';receipt['native_packed_const_unit_argv']=packed_argv
 receipt['status']='prepared' 
except Exception as e:receipt.update(status='failed_or_capped',error=repr(e))
finally:
 (OUT/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps({'status':receipt['status']}),flush=True)
if receipt['status']!='prepared':raise SystemExit(1)

# Fixed development capture only, after all native correctness gates.
subprocess.run(['python3',str(HERE/'profile_optimized.py'),'--binary',str(binary)],check=True,timeout=180)
