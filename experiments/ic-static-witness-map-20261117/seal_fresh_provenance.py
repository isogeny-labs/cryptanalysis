#!/usr/bin/env python3
"""Seal completed runner metadata without backdating the generation receipt."""
import hashlib, io, json, os, subprocess, sys, tarfile
from pathlib import Path
import certifi
P=Path(__file__).resolve().parent; ROOT=P.parents[1]
os.environ['SSL_CERT_FILE']=certifi.where(); sys.path.insert(0,str(ROOT/'cloud')); import modal_run as remote
job='20261117-103835-fc0d'; volume=remote.volume()
sha=lambda b:hashlib.sha256(b).hexdigest()
metadata=remote.read_bytes(volume,job+'/job.json'); m=json.loads(metadata)
assert metadata==(P/'timing-launch-metadata.json').read_bytes()
assert not m['git']['dirty'] and m['git']['commit']=='23c8e3c8f11a8d62b1a948cd51d944523dd51aec'
status=remote.read_bytes(volume,job+'/shards/0/status.json'); assert json.loads(status)['returncode']==0
assert json.loads((P/'timing-optimized-001/summary.json').read_text())['status']=='matrix_completed_unqualified'
snapshot=remote.read_bytes(volume,job+'/src.tar.gz'); host=json.loads((P/'timing-optimized-001/host.json').read_text())
with tarfile.open(fileobj=io.BytesIO(snapshot),mode='r:gz') as archive:
    for name,value in host['source_sha256'].items():
        raw=archive.extractfile(name).read(); assert sha(raw)==value
        assert raw==subprocess.check_output(['git','show',m['git']['commit']+':'+name],cwd=ROOT)
identities=P/'fresh-identities.json'; generator=P/'freeze_fresh_inputs.py'; probe=ROOT/'suite/target/debug/examples/ic_affine_pipeline_probe'
ids_revision=subprocess.check_output(['git','rev-parse','b08e124a01'],cwd=ROOT,text=True).strip()
assert identities.read_bytes()==subprocess.check_output(['git','show',ids_revision+':'+str(identities.relative_to(ROOT))],cwd=ROOT)
generation=dict(status='post_execution_provenance_audit',purpose='prepublished identities were checked against every native target; local ARM probe is identity generation only',published_admission_revision=subprocess.check_output(['git','rev-parse','a0a8111513'],cwd=ROOT,text=True).strip(),published_identities_revision=ids_revision,argv=['python3',str(generator.relative_to(ROOT)),str(probe.relative_to(ROOT))],local_probe_sha256_observed_now=sha(probe.read_bytes()),local_probe_hash_at_generation_recorded=False,limitation='No instantaneous local identity-probe hash receipt was saved at generation; this audit is retrospective. Exact candidate/workload IDs, four native binary bindings and protocol were published before timing; every native target matched those identities.',generator_sha256=sha(generator.read_bytes()),identities_sha256=sha(identities.read_bytes()),new_candidates=10,reused_candidates=25,one_target_workloads=210,fixtures=[684,725],native_preparation='20261117-095854-5065')
for name,data in [('fresh-native-job-metadata.json',metadata),('fresh-runner-status.json',status),('fresh-generation.json',(json.dumps(generation,indent=2)+'\n').encode()),('fresh-snapshot-binding.json',(json.dumps(dict(status='pass',snapshot_sha256=sha(snapshot),runner_status_sha256=sha(status),metadata_sha256=sha(metadata),frozen_source_revision=m['git']['commit'],source_files_checked=len(host['source_sha256'])),indent=2)+'\n').encode())]:
    path=P/name; assert not path.exists(); path.write_bytes(data)
print(json.dumps(dict(status='pass',source_files_checked=len(host['source_sha256']),local_probe_hash_receipt='retrospective limitation explicitly retained')))
