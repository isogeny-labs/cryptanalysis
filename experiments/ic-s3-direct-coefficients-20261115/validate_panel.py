#!/usr/bin/env python3
"""Recompute raw paired summaries; no independent timing qualification."""
import hashlib
import json
from pathlib import Path
import statistics

HERE=Path(__file__).resolve().parent
summary=json.loads((HERE/'run-001/summary.json').read_text())
raw=list((HERE/'native-001').glob('*'))
heads=[]
if summary['status']=='exploratory_unqualified':
 pairs=json.loads((HERE/'run-001/pairs.json').read_text())
 assert len(pairs)==30
 for p in pairs:
  a,b=(p['runs'][v]['result'] for v in ['reference','direct'])
  assert a['checksum']==b['checksum'] and p['checksum_equal']
  assert a['equation_checks']==b['equation_checks']==32
  assert (a['n'],a['np'],a['fixture'],a['summands'])==(b['n'],b['np'],b['fixture'],b['summands'])
  assert not a['feature'] and b['feature']
  for key,timer in [('raw_cold_ratio','cold_stage_s'),('raw_build_ratio','first_build_s')]:
   ratio=a[timer]/b[timer]
   assert abs(p[key]-ratio)<=1e-12*ratio
  assert p['qualified_ratio'] is None
 for c in summary['cases']:
  selected=[p for p in pairs if (p['n'],p['np'],p['summands'])==(c['n'],c['np'],c['summands'])]
  assert len(selected)==6
  for claim,key in [('raw_cold_median','raw_cold_ratio'),('raw_build_median','raw_build_ratio')]:
   value=statistics.median(p[key] for p in selected)
   assert abs(c[claim]-value)<1e-12*value
   heads.append({'name':f"n{c['n']}-np{c['np']}-m{c['summands']}-{claim}", 'claimed':c[claim],'recomputed':value})
 raw += list((HERE/'run-001').glob('*'))
 assert summary['qualified'] is None
else:
 assert summary['status']=='failed_or_capped'
 raw += list((HERE/'run-001').glob('*'))
 heads.append({'name':'complete_pairs','claimed':summary['pairs'],'recomputed':len(json.loads((HERE/'run-001/pairs.json').read_text())) if (HERE/'run-001/pairs.json').exists() else 0})
report={'schema':'ic-s3-producer-recompute/v1','status':'pass','timing_qualified':False,
        'raw_data':[{'path':str(p.relative_to(HERE)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(raw) if p.is_file()],
        'headline':heads,'standing':'unsigned producer recomputation; not independent validation'}
(HERE/'validation.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'status':'pass','headline_values':len(heads),'timing_qualified':False}))
