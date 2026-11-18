#!/usr/bin/env python3
"""Bind native setup admission to its clean published source and full snapshot."""
import argparse,hashlib,io,json,os,subprocess,sys,tarfile
from pathlib import Path
import certifi
P=Path(__file__).resolve().parent;ROOT=P.parents[1]
os.environ['SSL_CERT_FILE']=certifi.where();sys.path.insert(0,str(ROOT/'cloud'));import modal_run as remote
from source_manifest import changed_sources
p=argparse.ArgumentParser();p.add_argument('job');a=p.parse_args();sha=lambda b:hashlib.sha256(b).hexdigest()
rpath=P/'setup-build-001/receipt.json';r=json.loads(rpath.read_text());assert r['status']=='prepared'
assert sha((P/'setup-build-001/probe').read_bytes())==r['binary_sha256']
mb=remote.read_bytes(remote.volume(),a.job+'/job.json');m=json.loads(mb)
sb=remote.read_bytes(remote.volume(),a.job+'/shards/0/status.json');status=json.loads(sb)
assert status['returncode']==0 and m['git']['commit']==r['source_commit'] and not m['git']['dirty']
assert m['gpu']=='L4' and m['cpu']==4 and m['memory_gib']==8
assert json.loads((P/'setup-cell-smoke-001/summary.json').read_text())['answers']==20
assert all(x['setup_control_map_comparisons']==15 for x in r['native_table_smoke'])
old=json.loads((P/'baseline-source-hashes.json').read_text())
assert {n for n in old if old[n]!=r['source_sha256'][n]}==set(changed_sources)
snapshot=remote.read_bytes(remote.volume(),a.job+'/src.tar.gz');assert snapshot
names=[*changed_sources,*[str((P/f).relative_to(ROOT)) for f in ['build_setup_native.py','source_manifest.py','counterfactual_checks.py','verify_setup_state_cells.py','verify_frozen_units.py','instances.json','baseline-input.json','baseline-source-hashes.json','SETUP_STATE_PLAN.md']]]
with tarfile.open(fileobj=io.BytesIO(snapshot),mode='r:gz') as archive:
 for n in names:
  data=archive.extractfile(n).read();assert data==subprocess.check_output(['git','show',m['git']['commit']+':'+n],cwd=ROOT),n
  if n in changed_sources:assert sha(data)==r['source_sha256'][n]
pin=dict(status='pass',runner_status_sha256=sha(sb),source_job=a.job,source_commit=m['git']['commit'],receipt_source_commit=r['source_commit'],binary_sha256=r['binary_sha256'],receipt_sha256=sha(rpath.read_bytes()),job_metadata_sha256=sha(mb),snapshot_sha256=sha(snapshot),snapshot_git_fields_checked=len(names),purpose='Native setup-state correctness admission only; no timing or performance result')
for name,data in [('setup-input.json',json.dumps(pin,indent=2).encode()+b'\n'),('setup-native-job-metadata.json',mb),('setup-runner-status.json',sb)]:
 target=P/name;assert not target.exists();target.write_bytes(data)
print(json.dumps(pin))
