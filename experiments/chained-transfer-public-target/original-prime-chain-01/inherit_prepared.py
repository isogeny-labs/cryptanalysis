"""Pin unchanged dependency preparation after the wrapper-only import repair."""
from pathlib import Path
import json,hashlib,os,sys,shutil,stat
prior,out=map(Path,sys.argv[1:3]);pkg=Path(__file__).resolve().parent
assert(prior/'original-engine-preparation.exit').read_text().strip()=='0';assert(prior/'chain-compile.exit').read_text().strip()=='101'
for n in ['Cargo.toml','Cargo.lock']:assert(pkg/n).read_bytes()==(prior/'actual-source'/n).read_bytes()
a=json.loads((prior/'metadata.txt').read_text());b=json.loads((out/'metadata.txt').read_text());assert a['resolve']==b['resolve']
for old,new in zip(a['packages'],b['packages']):
 for k in ['id','manifest_path','dependencies','features','targets']:assert old[k]==new[k],(old['id'],k)
record=json.loads((prior/'engine-prepared.json').read_text());dest=out/'actual-prepared-original-engine';dest.mkdir();links=[]
for row in record['files']:
 actual=Path(row['actual_path']);before=Path(row['copy']);target=dest/before.name;body=actual.read_bytes();assert body==before.read_bytes();assert len(body)==row['bytes']and hashlib.sha256(body).hexdigest()==row['sha256'];os.link(before,target);assert target.read_bytes()==body
 links.append(dict(original_preparation_copy=str(before),new_full_copy=str(target),actual_cache_path=str(actual),bytes=len(body),sha256=row['sha256'],whole_before_after_equal=True));row['copy']=str(target)
(out/'engine-prepared.json').write_text(json.dumps(record,indent=2)+'\n');(out/'inherited-preparation.json').write_text(json.dumps(dict(original_build=str(prior),original_engine_preparation_exit=0,unchanged_Cargo_manifests_and_resolved_dependency_graph=True,files=links,scope='NO second engine preparation or cold claim; exact full closed copies linked only after entire independent cache-copy byte comparisons'),indent=2)+'\n')
