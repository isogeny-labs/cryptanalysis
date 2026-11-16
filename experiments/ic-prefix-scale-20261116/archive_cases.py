#!/usr/bin/env python3
"""Canonical archives through the existing builder, with append-only index bytes."""
import csv,hashlib,io,json,sys
from pathlib import Path
import yaml
P=Path(__file__).resolve().parent;ROOT=P.parents[1]
sys.path.insert(0,str(ROOT/'experiments/fb-archive'));import fbarchive as archive
registry=yaml.safe_load((ROOT/'experiments/ic-candidate-catalog/curves.yaml').read_text())['curves']
plan=[(15,'icv1_f2m15_t131_ed7256f0'),(18,'icv1_f2m18_t393_d2c04152'),(21,'icv1_f2m21_t2591_de54d72e'),(24,'icv1_f2m24_tm3047_2d0c0e8c'),(27,'icv1_f2m27_t12543_569dca8b')]
index=archive.INDEX;before=index.read_bytes();assert before.endswith(b'\n'), 'index must end with a record separator';old=archive.read_index();rows=[];instances=[]
# store()'s ordinary index writer sorts rows. Route it to a new overlay while
# it creates canonical archive bytes; append verified rows to the global index.
overlay=P/'archive-index-added.csv'
if overlay.exists():raise ValueError('one-shot archive overlay already exists; inspect prior output')
archive.INDEX=overlay
try:
 for n,alias in plan:
  entry=registry[alias];assert entry['field']['degree']==n
  d=(n+2)//3+1
  if n in [15,18]:
   selected=[r for r in old if r['curve_id']==entry['curve_id'] and r['family']=='registry-prefix' and int(r['l'])==d and r['seed']=='0'];assert len(selected)==1;row=selected[0]
  else:
   row=archive.store(archive.build(n,'registry-prefix',d,0,True,extra={'registry_alias':alias}))
   errors=archive.verify_row(row,True,10000);assert not errors,errors
  rows.append(row)
  instances.append(dict(alias=alias,curve_id=entry['curve_id'],curve_uid=entry['curve_uid'],field=entry['field'],curve=entry['curve'],dimension=d,max_trials=500000))
finally:archive.INDEX=index
assert index.read_bytes()==before,'global index changed concurrently'
existing={r['path']:r for r in old};new=[]
for row in rows:
 if row['path'] in existing:
  assert {k:str(v) for k,v in row.items()}==existing[row['path']]
 else:new.append(row)
stream=io.StringIO(newline='');writer=csv.DictWriter(stream,fieldnames=archive.INDEX_FIELDS,lineterminator='\r\n' if before.splitlines(keepends=True)[0].endswith(b'\r\n') else '\n');writer.writerows(new)
with index.open('ab') as f:f.write(stream.getvalue().encode())
after=index.read_bytes();assert after.startswith(before)
for row in rows:
 errors=archive.verify_row(row,True,10000);assert not errors,errors
 (P/f"archive-n{row['n']}.json").write_text(json.dumps(row,indent=2)+'\n')
(P/'instances.json').write_text(json.dumps(instances,indent=2)+'\n')
receipt=dict(status='pass',added_rows=len(new),preserved_prefix_bytes=len(before),before_sha256=hashlib.sha256(before).hexdigest(),after_sha256=hashlib.sha256(after).hexdigest(),cases=[{k:r[k] for k in ['curve_id','n','l','fb_points','effective_columns','path']} for r in rows])
(P/'archive-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt,indent=2))
