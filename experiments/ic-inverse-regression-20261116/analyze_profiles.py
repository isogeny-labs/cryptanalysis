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
results=json.loads((D/'results.json').read_text());assert [r['method'] for r in results]==['anchor','current','inverse','inverse','current','anchor','rho-plain','rho-negation']
rows=[]
for result in results:
 path=D/(result['label']+'.callgrind');assert hashlib.sha256(path.read_bytes()).hexdigest()==result['capture_sha256']
 parsed=parse_capture(path);annotation=(D/(result['label']+'-inclusive-no.stdout')).read_text()
 m=re.search(r'^\s*([0-9,]+)\s+\([^)]*\)\s+PROGRAM TOTALS',annotation,re.M);assert m and int(m[1].replace(',',''))==parsed['ir']
 parsed.update(method=result['method'],label=result['label'],binary_sha256=result['binary_sha256']);rows.append(parsed)
totals={m:[r['ir'] for r in rows if r['method']==m] for m in ['anchor','current','inverse','rho-plain','rho-negation']}
groups={}
for method in ['anchor','current','inverse']:
 selected=[r for r in rows if r['method']==method];own=collections.Counter()
 for r in selected:
  for f in r['functions']:own[f['function']]+=f['ir']/len(selected)
 groups[method]=own
deltas={}
for name,left,right in [('current_minus_anchor','current','anchor'),('inverse_minus_current','inverse','current')]:
 deltas[name]=sorted([dict(function=k,delta_ir=groups[left][k]-groups[right][k],left_ir=groups[left][k],right_ir=groups[right][k]) for k in groups[left].keys()|groups[right].keys()],key=lambda x:abs(x['delta_ir']),reverse=True)
r=dict(status='pass',qualified=None,scope='whole-guest Ir, exclusive symbols and separate call edges; not native wall/hardware retired/collector-only cost',totals=totals,rows=rows,exclusive_deltas=deltas)
(P/f'analysis-{args.run_id}.json').write_text(json.dumps(r,indent=2)+'\n')
print(json.dumps({'status':r['status'],'totals':totals,'top_deltas':{k:v[:15] for k,v in deltas.items()}}))

