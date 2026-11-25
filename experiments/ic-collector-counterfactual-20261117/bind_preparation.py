#!/usr/bin/env python3
"""Admit the exact binary, effective sources and full clean source snapshot."""
import argparse,hashlib,io,json,os,subprocess,sys,tarfile
from pathlib import Path
import certifi
P=Path(__file__).resolve().parent;ROOT=P.parents[1]
os.environ['SSL_CERT_FILE']=certifi.where();sys.path.insert(0,str(ROOT/'cloud'));import modal_run as remote
from source_manifest import hashes,changed_sources
p=argparse.ArgumentParser();p.add_argument('job');a=p.parse_args();sha=lambda b:hashlib.sha256(b).hexdigest()
rpath=P/'build-001/receipt.json';r=json.loads(rpath.read_text());assert r['status']=='prepared' and r['source_sha256']==hashes()
binary=P/'build-001/probe';assert sha(binary.read_bytes())==r['binary_sha256']
mb=remote.read_bytes(remote.volume(),a.job+'/job.json');m=json.loads(mb)
status_bytes=remote.read_bytes(remote.volume(),a.job+'/shards/0/status.json');assert json.loads(status_bytes)['returncode']==0
for directory in ['profile-n24-001']:
 assert json.loads((P/directory/'summary.json').read_text())['status']=='completed_unqualified'
assert m['git']['commit']==r['source_commit'] and not m['git']['dirty']
assert m['gpu']=='L4' and m['cpu']==4 and m['memory_gib']==8
assert json.loads((P/'cell-smoke-001/summary.json').read_text())['answers']==20
snapshot=remote.read_bytes(remote.volume(),a.job+'/src.tar.gz');assert snapshot
with tarfile.open(fileobj=io.BytesIO(snapshot),mode='r:gz') as archive:
 for name in [*changed_sources,*[str((P/f).relative_to(ROOT)) for f in ['build_native.py','source_manifest.py','profile_n24.py','counterfactual_checks.py','verify_counterfactual_cells.py','verify_frozen_units.py','profile-result-input.json']]]:
  data=archive.extractfile(name).read();exact=subprocess.check_output(['git','show',m['git']['commit']+':'+name],cwd=ROOT);assert data==exact,name
  if name in changed_sources:assert sha(data)==r['source_sha256'][name]
pin=dict(runner_status_sha256=sha(status_bytes),source_job=a.job,source_commit=m['git']['commit'],receipt_source_commit=r['source_commit'],binary_sha256=r['binary_sha256'],receipt_sha256=sha(rpath.read_bytes()),job_metadata_sha256=sha(mb),snapshot_sha256=sha(snapshot),purpose='native correctness preparation, effective source recipe and full clean snapshot admitted; no timing result')
for path,data in [(P/'optimized-input.json',json.dumps(pin,indent=2).encode()+b'\n'),(P/'preparation-job-metadata.json',mb)]:
 if path.exists():assert path.read_bytes()==data,'immutable binding differs'
 path.write_bytes(data)
print(json.dumps(pin))
