#!/usr/bin/env python3
"""Cross-check complete guest Ir and exclusive/call-edge attribution."""
import argparse,collections,hashlib,json,re,statistics
from pathlib import Path
P=Path(__file__).resolve().parent
parser=argparse.ArgumentParser();parser.add_argument('--run-id',required=True);args=parser.parse_args();assert args.run_id.replace('-','').isalnum()
D=P/args.run_id

def parse_capture(path):
 lines=path.read_text().splitlines();events=next(x[8:].split() for x in lines if x.startswith('events: '));assert events==['Ir']
 positions=next(x[11:].split() for x in lines if x.startswith('positions: '));assert positions==['instr','line']
 summaries=[int(x[9:]) for x in lines if x.startswith('summary: ')];totals=[int(x[8:]) for x in lines if x.startswith('totals: ')];assert len(summaries)==len(totals)==1 and summaries==totals and totals[0]>0
 names={};own=collections.Counter();edges=[];current=None;callee=None;pending=None
 def reference(value):
  match=re.fullmatch(r'\((\d+)\)(?: (.*))?',value)
  if match:
   key=int(match[1])
   if match[2] is not None:
    assert key not in names or names[key]==match[2];names[key]=match[2]
   return key
  key='literal:'+value;names[key]=value;return key
 for line in lines:
  if line.startswith('fn='):
   assert pending is None;current=reference(line[3:])
  elif line.startswith('cfn='):callee=reference(line[4:])
  elif line.startswith('calls='):
   assert pending is None and callee is not None;pending=(callee,int(line[6:].split()[0]))
  elif re.match(r'^(?:0x[0-9a-f]+|[+-][0-9]+|\*)\s',line):
   parts=line.split();cost=int(parts[2]) if len(parts)>2 else 0
   assert current is not None
   if pending is not None:
    edges.append((current,pending[0],pending[1],cost));pending=None
   else:own[current]+=cost
 assert pending is None and sum(own.values())==totals[0],('exclusive Ir sum differs',sum(own.values()),totals[0])
 assert all(key in names for key in own) and all(a in names and b in names for a,b,_,_ in edges)
 functions=sorted((dict(function=names[key],ir=value,fraction=value/totals[0]) for key,value in own.items()),key=lambda x:x['ir'],reverse=True)
 inv_edges=sorted((dict(caller=names[a],callee=names[b],calls=n,ir=ir) for a,b,n,ir in edges if 'Gf2>::inv' in names[b]),key=lambda x:x['ir'],reverse=True)
 all_edges=sorted((dict(caller=names[a],callee=names[b],calls=n,ir=ir) for a,b,n,ir in edges),key=lambda x:x['ir'],reverse=True)
 return dict(call_edges=all_edges,ir=totals[0],exclusive_sum=sum(own.values()),functions=functions,inversion_call_edges=inv_edges,creator=next(x[9:] for x in lines if x.startswith('creator: ')))

summary=json.loads((D/'summary.json').read_text());assert summary['status']=='completed_unqualified'
results=json.loads((D/'results.json').read_text());assert [r['mode'] for r in results]==['mitm-walk16-native','mitm-walk16-vector','mitm-walk16-vector','mitm-walk16-native','rho-plain','rho-negation']
rows=[]
for result in results:
 path=D/(result['label']+'.callgrind');assert hashlib.sha256(path.read_bytes()).hexdigest()==result['capture_sha256']
 parsed=parse_capture(path)
 annotation=(D/(result['label']+'-inclusive-no.stdout')).read_text();m=re.search(r'^\s*([0-9,]+)\s+\([^)]*\)\s+PROGRAM TOTALS',annotation,re.M);assert m and int(m[1].replace(',',''))==parsed['ir']
 raw=result['result'];report=raw['solver'] if result['mode'].startswith('rho-') else raw['report']['Ok']
 assert report['verified'] and report['recovered']==raw['planted']
 parsed.update(mode=result['mode'],label=result['label'],capture_sha256=result['capture_sha256'])
 if not result['mode'].startswith('rho-'):
  parsed['setup_native']=report['decomposition']['setup']['native'];parsed['query_native']=report['decomposition']['cost']['native'];parsed['rank']=report['linear_algebra']['rank']
 rows.append(parsed)
batch16=[r['ir'] for r in rows if r['mode']=='mitm-walk16-native'];vector16=[r['ir'] for r in rows if r['mode']=='mitm-walk16-vector'];assert len(batch16)==len(vector16)==2
r=dict(status='pass',run_id=args.run_id,qualified=None,scope='whole-guest instruction-read events; not native wall time/hardware retirement/primary-online interval',rows=rows,batch16_ir=batch16,vector16_ir=vector16,batch16_median_ir=statistics.median(batch16),vector16_median_ir=statistics.median(vector16),supplementary_batch16_over_vector16_ir_ratio=statistics.median(batch16)/statistics.median(vector16),repeated_ir_relative_ranges=dict(batch16=(max(batch16)-min(batch16))/statistics.median(batch16),vector16=(max(vector16)-min(vector16))/statistics.median(vector16)))
(P/f'analysis-{args.run_id}.json').write_text(json.dumps(r,indent=2)+'\n')
print(json.dumps({k:v for k,v in r.items() if k!='rows'}))
for row in rows:
 print(row['label'],'Ir',row['ir'],'top',[(x['function'],x['ir']) for x in row['functions'][:6]],'inv_edges',row['inversion_call_edges'][:5])
