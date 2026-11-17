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

assert json.loads((D/'summary.json').read_text())['status']=='completed_unqualified'
results=json.loads((D/'results.json').read_text());assert [r['method'] for r in results]==['current','inverse']
rows=[]
for result in results:
 path=D/(result['label']+'.callgrind');assert hashlib.sha256(path.read_bytes()).hexdigest()==result['capture_sha256']
 parsed=parse_capture(path);annotation=(D/(result['label']+'-inclusive-no.stdout')).read_text()
 match=re.search(r'^\s*([0-9,]+)\s+\([^)]*\)\s+PROGRAM TOTALS',annotation,re.M);assert match and int(match[1].replace(',',''))==parsed['ir']
 parsed.update(method=result['method'],label=result['label'])
 parsed['generic_dispatch_exclusive_ir']=sum(f['ir'] for f in parsed['functions'] if 'ic_boundary::decompose_mitm::' in f['function'])
 parsed['generic_dispatch_edges']=[e for e in parsed['call_edges'] if 'ic_boundary::decompose_mitm::' in e['callee']]
 assert parsed['generic_dispatch_exclusive_ir']==0 and not parsed['generic_dispatch_edges']
 rows.append(parsed)
for row in rows:
 row['walker_wide_remainder_edges']=[e for e in row['call_edges'] if 'BatchedWalker' in e['caller'] and '::next' in e['caller'] and '__umodti3' in e['callee']]
 assert not row['walker_wide_remainder_edges'], 'hot coefficient remainder calls remain'
out={'status':'pass','rows':rows,'scope':'whole-guest instrumented Ir; not native timing; no cross-panel wall-time inference','qualification':None}
(P/'analysis-post-profile.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({'status':out['status'],'ir':{r['method']:r['ir'] for r in rows}}))
