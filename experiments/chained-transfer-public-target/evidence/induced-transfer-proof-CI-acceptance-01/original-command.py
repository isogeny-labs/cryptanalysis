"""Whole fresh proof-CI transport/custody and exact original receipt validation; no mathematics."""
from pathlib import Path,PurePosixPath
from datetime import datetime,timezone
import hashlib,json,os,shutil,subprocess,urllib.request,zipfile
r=Path('/workspace/cryptanalysis');study=r/'experiments/chained-transfer-public-target';ci=study/'ci_induced_transfer';out=Path('/workspace/scratch/ct95-induced-proof-CI-acceptance-01')
shutil.copyfile(__file__,out/'original-command.py')
api=json.loads(Path('/workspace/scratch/private-ct95-induced-proof-download-api.json').read_text());data=api.get('structuredContent',api)
if 'file_uri'not in data:data=data['structuredContent']
zpath=out/'whole-original-artifact.zip';assert not zpath.exists()
with urllib.request.urlopen(data['file_uri']['download_url'],timeout=120)as a,zpath.open('xb')as b:shutil.copyfileobj(a,b)
def digest(p):
 with p.open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
assert zpath.stat().st_size==24931 and digest(zpath)=='8522fa8a217f017d87c83135a3248b893532a3380240cbbd2cee7d212bfa2d16'
p=out/'whole-artifact';p.mkdir();rows=[]
with zipfile.ZipFile(zpath)as z:
 assert len(z.namelist())==len(set(z.namelist()))
 for info in z.infolist():
  rel=PurePosixPath(info.filename);assert not rel.is_absolute()and'..'not in rel.parts and'\\'not in info.filename and not info.is_dir()
  b=z.read(info);f=p/info.filename;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes(b)
  rows.append(dict(path=info.filename,bytes=len(b),sha256=hashlib.sha256(b).hexdigest(),CRC=info.CRC))
(out/'all-whole-artifact-members.json').write_text(json.dumps(rows,indent=2)+'\n')
assert(p/'consumer-head.txt').read_text().strip()=='41e35d8c701484a6ca5406ecbf7bb83278be6073'
assert(p/'producer-head.txt').read_text().strip()=='3d49af7f3d0a28e76b79e4825c9d2324e85853d2'
assert(p/'original.exit').read_text().strip()==(p/'final-source-guards.exit').read_text().strip()=='0'
assert(p/'original-command.sh').read_bytes()==(ci/'check-01.sh').read_bytes()
assert(p/'original-reference.sha256').read_bytes()==(ci/'reference-01.sha256').read_bytes()
refs=(p/'original-reference.sha256').read_text().splitlines();assert len(refs)==73
for line in refs:
 h,name=line.split('  ',1);assert digest(r/name)==h,name
phases=[line.split()for line in(p/'phases.txt').read_text().splitlines()];assert len(phases)==16
for name,code in phases:
 assert code=='0'and(p/(name+'.pipe-exits')).read_text().split()==['0','0']
host=out/'independent-complete-receipt-check';shutil.copytree(p,host);(host/'whole-proof-coverage-and-bindings.json').unlink()
cmd=['python3',str(ci/'validate_receipts_01.py'),str(r),str(host)]
q=subprocess.run(cmd,capture_output=True);(out/'independent-validator.txt').write_bytes(q.stdout+q.stderr);(out/'independent-validator.exit').write_text(str(q.returncode)+'\n');assert q.returncode==0
assert(host/'whole-proof-coverage-and-bindings.json').read_bytes()==(p/'whole-proof-coverage-and-bindings.json').read_bytes()
logpath=out/'whole-original-runlogs.zip';cmd=['timeout','120','gh','api','repos/isogeny-labs/cryptanalysis/actions/runs/43707728617/logs']
with logpath.open('xb')as dest,Path('/workspace/scratch/private-ct95-proof-runlogs.stderr').open('xb')as err:q=subprocess.run(cmd,stdout=dest,stderr=err)
(out/'whole-runlogs-download.exit').write_text(str(q.returncode)+'\n');assert q.returncode==0
logs=[]
with zipfile.ZipFile(logpath)as z:
 for info in z.infolist():
  h=hashlib.sha256();size=0
  with z.open(info)as f:
   while chunk:=f.read(1048576):h.update(chunk);size+=len(chunk)
  assert size==info.file_size;logs.append(dict(path=info.filename,bytes=size,sha256=h.hexdigest(),CRC=info.CRC))
(out/'all-whole-runlog-members.json').write_text(json.dumps(logs,indent=2)+'\n')
acceptance=dict(at=datetime.now(timezone.utc).isoformat(),source='41e35d8c701484a6ca5406ecbf7bb83278be6073',producer='3d49af7f3d0a28e76b79e4825c9d2324e85853d2',run=43707728617,job=132792341744,artifact=14159515706,whole_artifact_bytes=24931,whole_artifact_sha256=digest(zpath),all_original_members=len(rows),whole_runlogs_bytes=logpath.stat().st_size,whole_runlogs_sha256=digest(logpath),whole_runlog_members=len(logs),all16phases_expected0=True,all73source_guards0=True,both_original_gates_all21_declarations_0trusted=True,nine_named_and12_structural=True,allnine_exact_statement_bindings_pass=True,whole_actual_consumer_and_producer_source_bytes_equal=True,independent_actual_versioned_validator_exit=0,independently_reproduced_complete_verdict_bytes=True,scope='unsigned exact additive proof-CI replay; conditional quotient algebra only, actual model-field-Frobenius-Picard-order-program-lift and calibrated-cost obligations remain explicit; no all-current/global CI or ECDLP-advantage/signed standing')
(out/'acceptance.json').write_text(json.dumps(acceptance,indent=2)+'\n');print(json.dumps(acceptance),flush=True)
