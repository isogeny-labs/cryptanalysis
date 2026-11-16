"""Compare the exact field-engine dependency closure and full prepared bytes."""
from pathlib import Path
import hashlib,json,os,sys
prior,out=map(Path,sys.argv[1:3])
assert(prior/'original.exit').read_text().strip()=='0'
a=json.loads((prior/'metadata.txt').read_text());b=json.loads((out/'metadata.txt').read_text())
def closure(metadata):
 packages={p['id']:p for p in metadata['packages']};nodes={n['id']:n for n in metadata['resolve']['nodes']}
 roots=[p['id']for p in packages.values()if Path(p['manifest_path']).resolve()==Path('/workspace/crypto/isogeny_algos/Cargo.toml').resolve()]
 assert len(roots)==1
 seen=set();pending=roots[:]
 while pending:
  key=pending.pop()
  if key in seen:continue
  seen.add(key);pending.extend(d['pkg']for d in nodes[key]['deps'])
 return {key:dict(node=nodes[key],package={name:packages[key][name]for name in ['id','manifest_path','dependencies','features','targets']})for key in sorted(seen)}
old,new=closure(a),closure(b);assert old==new,'field-engine dependency/features/targets changed; do not reuse preparation'
record=json.loads((prior/'engine-prepared.json').read_text());dest=out/'actual-prepared-original-engine';dest.mkdir();links=[]
for row in record['files']:
 actual=Path(row['actual_path']);before=Path(row['copy']);target=dest/before.name;body=actual.read_bytes()
 assert body==before.read_bytes()and len(body)==row['bytes']and hashlib.sha256(body).hexdigest()==row['sha256']
 os.link(before,target);assert target.read_bytes()==body
 links.append(dict(previous_full_closed_copy=str(before),actual_cache_path=str(actual),new_full_copy=str(target),bytes=len(body),sha256=row['sha256'],whole_independent_comparison=True));row['copy']=str(target)
(out/'engine-prepared.json').write_text(json.dumps(record,indent=2)+'\n')
(out/'inherited-preparation.json').write_text(json.dumps(dict(prior=str(prior),exact_whole_engine_dependency_closure=old,all_dependency_feature_target_identities_equal=True,files=links,no_new_engine_preparation=True,scope='full cache/prepared-copy equality; closed copies linked after independent byte comparison'),indent=2)+'\n')
