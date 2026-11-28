"""Frozen follow-up analysis; native reports only, no research arithmetic."""
from pathlib import Path
import json,hashlib,math,random,statistics
HERE=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def gm(v):return math.exp(statistics.mean(map(math.log,v)))
def ci(v):
 r=random.Random(1729);z=list(map(math.log,v));a=sorted(math.exp(statistics.mean(r.choices(z,k=len(z)))) for _ in range(10000));return [a[124],a[9874]]
def main():
 m=json.loads((HERE/'manifest.json').read_text());assert len(m['cells'])==32
 assert sha(HERE/'PROTOCOL.md')==m['protocol_sha256'] and sha(HERE/'seeds.json')==m['seeds_sha256']
 for c in m['cells']:
  assert sha(HERE/'raw'/(c['id']+'.txt'))==c['log_sha256']
  if c['stage']!='rho' and c['report'] is not None:assert sha(HERE/'raw'/(c['id']+'.json'))==c['report_sha256']
 rows=[];solved={a:0 for a in ('selected-aa0','selected-aa1','m3-reference','m4-reference')};ratios={a:[] for a in ('m3','m4')};noise=[];primary=[];rhot=[]
 for i in range(5):
  arms={c['arm']:c for c in m['cells'] if c['stage']=='heldout' and c['replicate']==i};row={'replicate':i}
  for arm,c in arms.items():
   r=c['report'];ok=r is not None and r['status']=='solved' and c.get('expected_scalar_match') and c['exit_code']==0
   solved[arm]+=int(bool(ok));row[arm]={'solved':bool(ok),'cold_ms':r['cold_to_report_ns']/1e6 if r else None,'queries':r['work']['queries'] if r else None,'relations':r['work']['relations'] if r else None,'peak_rss_mib':c['peak_rss_gib']*1024,'process_wall_ms':c['wall_s']*1000 if 'wall_s' in c else c.get('wall_seconds',0)*1000}
   if r:assert r['cold_to_report_ns']>=sum(r[k] for k in ('base_construction_ns','group_preparation_ns','pair_index_ns','online_ns','extra_certificate_replay_ns'))
  a=row['selected-aa0'];b=row['selected-aa1']
  if a['solved'] and b['solved']:
   assert arms['selected-aa0']['report']['certificate']==arms['selected-aa1']['report']['certificate'];assert arms['selected-aa0']['report']['work']==arms['selected-aa1']['report']['work'];noise.append(b['cold_ms']/a['cold_ms'])
  if a['solved']:
   primary.append(a['cold_ms'])
   for name in ratios:
    ref=row[name+'-reference']
    if ref['solved']:ratios[name].append(a['cold_ms']/ref['cold_ms'])
  rr=next(c for c in m['cells'] if c['stage']=='rho' and c['replicate']==i);r=rr['report'];assert r['rho']['status']=='solved' and rr['expected_scalar_match'];rhot.append(r['cli_accounting']['reference']/1e6);row['rho_reference_call_ms']=rhot[-1];rows.append(row)
 p=next(c['report'] for c in m['cells'] if c['stage']=='profile');ph=p['phase_profile_ns'];assert ph['total']==sum(v for k,v in ph.items() if k not in ('total','clock_reads'))
 comparisons={k:{'complete_pairs':len(v),'selected_over_reference_geomean':gm(v) if v else None,'conditional_family_bootstrap':ci(v) if v else None} for k,v in ratios.items()}
 recommend=solved['selected-aa0']==5 and statistics.median(primary)<1000 and all(len(v)==5 and gm(v)<1 for v in ratios.values())
 out={'schema':'m31-e2e-m2-result/v1','standing':'pcc:unverified','selected':json.loads((HERE/'selection.json').read_text())['selected'],'solved':solved,'rows':rows,'median_cold_ms':statistics.median(primary) if primary else None,'range_cold_ms':[min(primary),max(primary)] if primary else None,'comparisons':comparisons,'aa_repeatability_ratio_range':[min(noise),max(noise)] if noise else None,'median_rho_reference_call_ms':statistics.median(rhot),'selected_cold_over_rho_call_geomean':gm([row['selected-aa0']['cold_ms']/row['rho_reference_call_ms'] for row in rows if row['selected-aa0']['solved']]),'recommend_m2_on_this_panel':recommend,'profile':p,'host_qualification':'exploratory shared host; no admitted isolation; five targets, conditional intervals; panels not pooled','source_commit':m['source_commit']}
 (HERE/'summary.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items() if k not in ('rows','profile')},indent=2))
if __name__=='__main__':main()
