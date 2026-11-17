"""Existing exclusive Ir/call-edge parser, copied without metric changes."""
import collections,re
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
