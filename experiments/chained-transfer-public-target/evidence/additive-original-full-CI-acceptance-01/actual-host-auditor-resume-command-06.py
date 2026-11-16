"""Resume only uncompleted downloaded Rust auditor controls with the original fixture environment."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,os,shutil,stat,subprocess
r=Path('/workspace/cryptanalysis');s=r/'experiments/chained-transfer-public-target'
out=Path('/workspace/scratch/ct94-additive-original-full-CI-acceptance-01');p=out/'whole-artifact'
source='25801fe6aaba49674ef010e814dc7c9a58c28247';producer='3d49af7f3d0a28e76b79e4825c9d2324e85853d2'
failed=out/'independent-audit-failed05';failed.mkdir()
for name in ['ct94_audit_complete_CI03_05.py','ct94-whole-CI-audit-caller05.txt','ct94-whole-CI-audit-caller05.exit']:
 shutil.copyfile('/workspace/scratch/'+name,failed/name)
(failed/'classification.txt').write_text('All static custody checks passed. First18 host Rust controls passed (four whole positives/fourteen actual omissions). Kernel positive101 then reported missing N4_ORIGINAL_KERNEL_INPUTS before accepting output. The host launcher omitted the existing documented fixture environment. Preserve full failure; resume only the remaining13 controls with the same immutable source pin and whole downloaded fixtures used by CI. No CI result, fixture, Rust code, expected output or criterion changes.\n')
shutil.copyfile(__file__,out/'actual-host-auditor-resume-command-06.py')
def digest(f):
 with f.open('rb')as q:return hashlib.file_digest(q,'sha256').hexdigest()
def equal(a,b):
 if a.stat().st_size!=b.stat().st_size:return False
 with a.open('rb')as x,b.open('rb')as y:
  while True:
   u,v=x.read(1048576),y.read(1048576)
   if u!=v:return False
   if not u:return True
results=json.loads((out/'host-controls-progress.json').read_text());assert len(results)==18
assert len([v for v in results if v['actual_exit']==0])==4
assert json.loads((out/'independent-custody-checks.json').read_text())['all_checks_above_pass']is True
links=[]
for row in results:
 exe=Path(row['command'][2]);compiled=next(v for v in json.loads((out/'independent-custody-checks.json').read_text())['binaries']if v['compiled']==exe.name)
 assert digest(exe)==compiled['sha256']
 if row['actual_exit']==0:
  target=Path(row['command'][-1]);original=p/(row['label']+'-all-whole-records.json')
  assert equal(target,original)and target.stat().st_ino==original.stat().st_ino
  links.append(dict(path=str(target),original=str(original),bytes=target.stat().st_size,sha256=digest(target),whole_generation_comparison_before_link_in_original05=True))
host=out/'actual-downloaded-Rust-auditor-controls-02';host.mkdir()
env=dict(os.environ,N4_ORIGINAL_KERNEL_INPUTS=str(p/'original-kernel-fixtures'),N4_ORIGINAL_KERNEL_SOURCE='811395139bbd33b75fd5697973202cd1dcc13bba',N4_ORIGINAL_PRIME_FIXTURES=str(p/'original-prime-fixtures'),N4_ORIGINAL_FULL_MODEL_FIXTURES=str(p/'original-geometry-fixtures'))
sets=[('original-kernel',['N4_ORIGINAL_KERNEL_TRANSPORT','N4_ORIGINAL_KERNEL_VERTEX','N4_ORIGINAL_KERNEL_PAIR','N4_ORIGINAL_KERNEL_TRIPLE']),('original-geometry',['N4_CHAIN_FIXED_GEOMETRY']),('original-full',['N4_FIXED_CHAIN_EXCEPTIONAL_CASE','N4_FIXED_CHAIN_ALL_EXCEPTIONALS','N4_FIXED_CHAIN_ALL_PUBLIC','N4_FIXED_CHAIN_SELECTED_CALL_VECTORS','N4_ORIGINAL_FULL_KNOWN_POINT_VECTORS'])]
for label,tags in sets:
 exe=p/('actual-compiled-'+label+'-auditor.bin');before=digest(exe)
 prefix=[]if label=='original-kernel'else[p/'old-sixteen.json']
 if label=='original-geometry':prefix.append(p/'geometry-expected.json')
 cases=[('whole-positive',p/(label+'-native.txt'),0)]+[(tag,p/(label+'-'+tag+'-entire-actual-records-omitted.txt'),101)for tag in tags]
 for name,native,want in cases:
  target=host/(label+'-'+name+'-accepted.json');assert not target.exists()
  cmd=['timeout','120',str(exe),'--compare',*[str(v)for v in prefix],str(p/(label+'-expected.json')),str(native),str(target)]
  with(host/(label+'-'+name+'.txt')).open('xb')as log:q=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT,env=env,umask=0o077)
  (host/(label+'-'+name+'.exit')).write_text(str(q.returncode)+'\n')
  assert q.returncode==want,(label,name,q.returncode)
  if want:assert not target.exists()
  else:
   original=p/(label+'-all-whole-records.json');assert equal(target,original)
   assert stat.S_IMODE(target.stat().st_mode)==stat.S_IMODE(original.stat().st_mode)
   links.append(dict(path=str(target),original=str(original),bytes=target.stat().st_size,sha256=digest(target),whole_independently_generated_bytes_compared_before_link=True))
   temporary=target.with_name(target.name+'.closed-link');os.link(original,temporary);os.replace(temporary,target)
  results.append(dict(label=label,case=name,command=cmd,actual_exit=q.returncode,accepted_output=target.exists(),original_fixture_environment=env['N4_ORIGINAL_KERNEL_SOURCE']if label=='original-kernel'else 'same whole fixture files'))
  (out/'host-controls-progress-resumed06.json').write_text(json.dumps(results,indent=2)+'\n')
  print(label,name,q.returncode,flush=True)
 assert digest(exe)==before
assert len(results)==31 and len([v for v in results if v['actual_exit']==101])==24
for line in(p/'original-reference.sha256').read_text().splitlines():
 h,n=line.split('  ',1);assert digest(r/n)==h,n
(out/'host-positive-exact-byte-links.json').write_text(json.dumps(links,indent=2)+'\n')
counts=dict(zip(['geometry','chain','norm-point','original-prime','original-kernel','original-geometry','original-full'],[13,695,695,1077,311,16,701]))
acceptance=dict(at=datetime.now(timezone.utc).isoformat(),source=source,producer_pin=producer,run=43700115169,job=132769186550,artifact=14156900587,artifact_bytes=99483928,artifact_sha256='06104f175a79f38aa22961cabb6467e33838724e9e87f9b037e3477defa970fb',all_unfiltered_artifact_members=749,expected_phase_exits=153,whole_record_counts=counts,whole_class_omissions=24,original_source_guards=1440,both_original_proof_modules=12,both_original_proof_declaration_occurrences=70,distinct_proof_names=54,historical_repeated_proof_occurrences=16,all_exact_local_binding_verdicts=70,downloaded_actual_Rust_auditor_controls=results,whole_original_job_log_retained=True,actual_compiled_runtime_test_and_auditor_bytes_equal=True,full_prepared_RLIB_RMETA_and_complete_Cargo_closure_and_actual_reuse_checked=True,all_host_failures_preserved=True,scope='unsigned bounded exact CI03 replay and independent downloaded Rust auditor acceptance only; no induced-transfer proof CI, all-current/global CI, calibrated cost, cold120 acceptance, ECDLP advantage, or signed standing')
(out/'acceptance.json').write_text(json.dumps(acceptance,indent=2)+'\n')
print('COMPLETE CI03 ACCEPTANCE',json.dumps({k:v for k,v in acceptance.items()if k!='downloaded_actual_Rust_auditor_controls'}),flush=True)
