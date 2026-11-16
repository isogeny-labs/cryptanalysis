#!/usr/bin/env python3
"""Pin the already public development point and exact completed timing metadata."""
import hashlib,json,os,subprocess,sys
from pathlib import Path
import certifi
P=Path(__file__).resolve().parent;ROOT=P.parents[1]
os.environ['SSL_CERT_FILE']=certifi.where();sys.path.insert(0,str(ROOT/'cloud'))
import modal_run as remote
sha=lambda data:hashlib.sha256(data).hexdigest()
prepared=json.loads((P/'prepared-input.json').read_text());ids=json.loads((P/'identities.json').read_text())
workload_bytes=(ROOT/'experiments/ic-native-profile-20261116/workload.json').read_bytes();workload=json.loads(workload_bytes)
assert workload['fixture']==0 and workload['target_count']==1 and workload['curve_id']==json.loads((P/'instances.json').read_text())[4]['curve_id']
calibration=(P/'timing-001/calibration-4.json').read_bytes();assert json.loads(calibration)['curve_id']==workload['curve_id']
job='20261116-140621-6b2c';metadata_bytes=remote.read_bytes(remote.volume(),job+'/job.json');metadata=json.loads(metadata_bytes)
assert metadata['git']['commit']=='026ef4821a94fe6c1d0029a7b486656bc1223567'
candidates={}
for mode in ['mitm-walk16-native','mitm-walk16-vector']:
 filename=ids['4'][mode]+'.json';data=(ROOT/'experiments/ic-bench/candidates'/filename).read_bytes();candidate=json.loads(data)
 for path,pin in candidate['implementation']['sources_sha256'].items():
  source=subprocess.check_output(['git','show',prepared['source_commit']+':'+path]);assert sha(source)==pin
 candidates[filename]=sha(data)
doc=dict(schema='ic-vector-instruction-input/v1',prepared=prepared,timing_job=job,calibration_sha256=sha(calibration),timing_metadata_sha256=sha(metadata_bytes),instances_sha256=sha((P/'instances.json').read_bytes()),workload_sha256=sha(workload_bytes),candidates=candidates,purpose='fixed development point instruction attribution, not native wall timing')
for path,data in [(P/'profile-input.json',json.dumps(doc,indent=2).encode()+b'\n'),(P/'workload.json',workload_bytes),(P/'profile-timing-job-metadata.json',metadata_bytes)]:
 if path.exists():assert path.read_bytes()==data,'immutable profile input differs'
 path.write_bytes(data)
print(json.dumps(dict(status='frozen',development_fixture=0,methods=2,binary_sha256=prepared['binary_sha256'])))
