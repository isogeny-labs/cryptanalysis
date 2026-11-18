#!/usr/bin/env python3
"""Read every declared raw/report blob from the scoped store and hash its bytes."""
import concurrent.futures,hashlib,json,os,subprocess
from pathlib import Path
P=Path(__file__).resolve().parent;ROOT=P.parents[1]
r=json.loads((ROOT/'benchmarks/records/20261117T1809Z-ic-collector-buffer-state-eightpath-001.json').read_text());assert r['status']=='invalid' and len(r['raw'])==25
wanted={x['s3_uri']:{'sha256':x['s3_uri'].split('/')[-1],'bytes':x['bytes']} for x in r['raw']}
for name in [r['reports']['pdf'],*r['reports']['svg'],*r['reports']['png'],'benchmarks/progress/progress.pdf','benchmarks/progress/progress.svg']:
 f=ROOT/name;h=hashlib.sha256(f.read_bytes()).hexdigest();wanted['s3://crypto-autoresearcher/store/sha256/'+h[:2]+'/'+h]={'sha256':h,'bytes':f.stat().st_size}
env=dict(os.environ)
for k in ['AWS_ACCESS_KEY_ID','AWS_SECRET_ACCESS_KEY','AWS_SESSION_TOKEN','ARTIFACTS_AWS_ACCESS_KEY_ID','ARTIFACTS_AWS_SECRET_ACCESS_KEY']:env.pop(k,None)
env.update(AWS_PROFILE='default',AWS_REGION='us-west-2',AWS_DEFAULT_REGION='us-west-2')
def check(item):
 uri,expected=item;assert uri.startswith('s3://crypto-autoresearcher/store/sha256/')
 child=subprocess.Popen(['aws','s3','cp',uri,'-','--only-show-errors'],env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
 h=hashlib.sha256();size=0
 while chunk:=child.stdout.read(1048576):h.update(chunk);size+=len(chunk)
 error=child.stderr.read();assert child.wait()==0,(uri,error.decode())
 assert size==expected['bytes'] and h.hexdigest()==expected['sha256'],uri
 return {'uri':uri,**expected}
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:rows=list(pool.map(check,sorted(wanted.items())))
out=P/'setup-full-custody-readback.json';assert not out.exists()
out.write_text(json.dumps({'status':'pass','profile':'default','bucket':'crypto-autoresearcher','raw_references':25,'report_references':9,'progress_references':2,'unique_objects':len(rows),'bytes':sum(x['bytes'] for x in rows),'objects':rows,'scope':'Producer readback of every declared raw/report blob; native bundle member checks are separately retained; no independent signed standing'},indent=2)+'\n')
print(json.dumps({'status':'pass','objects':len(rows),'bytes':sum(x['bytes'] for x in rows)}))
