#!/usr/bin/env python3
"""Check only this record against its explicitly scoped store, never legacy defaults."""
import concurrent.futures,hashlib,importlib.util,json,os
from pathlib import Path
P=Path(__file__).resolve().parent;R=P.parents[1]
for k in ['AWS_ACCESS_KEY_ID','AWS_SECRET_ACCESS_KEY','AWS_SESSION_TOKEN','ARTIFACTS_AWS_ACCESS_KEY_ID','ARTIFACTS_AWS_SECRET_ACCESS_KEY']:os.environ.pop(k,None)
os.environ.update(AWS_PROFILE='default',AWS_REGION='us-west-2',AWS_DEFAULT_REGION='us-west-2',BENCHREC_S3_REGION='us-west-2')
s=importlib.util.spec_from_file_location('benchrec',R/'tools/benchrec.py');b=importlib.util.module_from_spec(s);s.loader.exec_module(b)
n='benchmarks/records/20261117T1809Z-ic-collector-buffer-state-eightpath-001.json';r=json.loads((R/n).read_text())
c=b.load_config(R);c['bucket']='crypto-autoresearcher';c['store_prefix']='store/sha256'
assert r['status']=='invalid' and len(r['raw'])==25 and len(r['metrics'])==180
m=b.artifact_manifests(R);wanted={x['s3_uri']:x['bytes'] for x in r['raw']}
reports=[r['reports']['pdf']]+r['reports'].get('svg',[])+r['reports'].get('png',[])
for name in reports:
 p=R/name;assert p.is_file();h=hashlib.sha256(p.read_bytes()).hexdigest();assert m[name]==h
 wanted[b.store_uri(c,h)]=p.stat().st_size
with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
 sizes=dict(zip(wanted,pool.map(lambda u:b.s3_head_size(u,c),wanted)))
assert sizes==wanted,(sizes,wanted)
i=b.S3Inventory(c);i.sizes.update(sizes)
errors=b.record_errors(R,c,r,n,require_closed=True,verify_s3=True,manifests=m,inventory=i)
assert not errors,errors
out=P/'setup-record-remote-check.json';assert not out.exists()
out.write_text(json.dumps(dict(status='pass',record=n,record_sha256=hashlib.sha256((R/n).read_bytes()).hexdigest(),raw_count=len(r['raw']),metric_count=len(r['metrics']),report_count=len(reports),objects=sizes,scope='Only current record and scoped working store; not global legacy remote validation'),indent=2)+'\n')
print(json.dumps(dict(status='pass',raw=25,metrics=180,reports=len(reports))))
