#!/usr/bin/env python3
"""Inspect archived model units without rewriting closed records or raw data."""
import hashlib,json
from pathlib import Path
P=Path(__file__).resolve().parent;ROOT=P.parents[1]
rows=[];sources={}
for study,name in [('ic-s3-pipeline-20261115','pairs.json'),('ic-affine-native-20261115','triples.json'),('ic-affine-columns-20261115','triples.json'),('ic-mitm-batch-20261115','triples.json')]:
 f=ROOT/'experiments'/study/'timing-001'/name;sources[str(f.relative_to(ROOT))]=hashlib.sha256(f.read_bytes()).hexdigest()
 for triple in json.loads(f.read_text()):
  for mode,arm in triple['runs'].items():
   raw=arm.get('result',{});r=raw.get('report',{}).get('Ok')
   if not r:continue
   native=r['decomposition']['cost']['native'];unit=raw['calibration']['ns_per_lookup']
   lookup=native.get('lookups',0);guard=native.get('target_guard_probes',0)
   rows.append(dict(study=study,index=triple['index'],fixture=triple['fixture'],mode=mode,
    lookup_count=lookup,guard_probes=guard,ns_per_lookup=unit,
    unpriced_lookup_work=bool(unit==0 and lookup+guard>0),cold_wall_s=raw['context_ns']*1e-9+r['wall_seconds']))
result=dict(schema='ic-probe-lookup-pricing-audit/v1',rows=rows,completed_ic_answers=len(rows),
 affected_answers=sum(r['unpriced_lookup_work'] for r in rows),source_sha256=sources,
 limitation='Model S excludes lookup/guard work when its conversion unit is zero; complete wall still includes it. Do not retroactively price old rows or promote them.',
 standing='unsigned producer source/data audit')
(P/'lookup-pricing-audit.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k not in ['rows','source_sha256']}))
