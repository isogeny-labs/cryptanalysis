"""Batch target-residual x tests for fixed-seed output-first pair recovery."""
import hashlib,itertools,json,resource,signal,sys,time
from pathlib import Path
from collections import Counter
ROOT=Path('/Volumes/SSD990/cryptanalysis/experiments/ecc2k130-ic-goal-20260929/output_first_fifth_20261019')
sys.path.insert(0,str(ROOT))
from output_first_math import FixedSeed
HERE=Path(__file__).resolve().parent
case=sys.argv[1];assert case in ('n41','n131')
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
cfg=json.loads((HERE/(case+'_fast_protocol.json')).read_text())
assert cfg['status']=='FROZEN_BEFORE_BATCH_OUTPUT_FAST_'+case.upper()
for k,v in cfg['sources'].items():assert sha(v['path'])==v['sha256'],k
assert cfg['worker_count']==1
signal.signal(signal.SIGALRM,lambda *_:(_ for _ in ()).throw(TimeoutError('wall cap')))
signal.alarm(cfg['wall_cap_seconds'])
start=time.monotonic()
if case=='n41':
 fixed=FixedSeed(41,[0,3],56,11);rotation=24
 panel=json.loads(Path(cfg['sources']['panel']['path']).read_text())
 states={}
 for line in Path(cfg['sources']['join_input']['path']).read_text().splitlines()[2:]:
  c=line.split()
  if c[0]=='S':
   slot,sid,code,branch,a,b,ca,cb,x,y=map(int,c[1:])
   states[(slot,sid)]={'point':(x,y),'code':code,'columns':[ca,cb]}
 boxes=[]
 for box in panel['boxes']:
  choices=[[states[(slot,sid)] for pair in box['root_choices'][slot] for sid in pair] for slot in range(4)]
  boxes.append({'kind':box['kind'],'choices':choices,'target':tuple(panel['target_point'])})
else:
 fixed=FixedSeed(131,[0,1,2,13],898618,33);rotation=72
 panel=json.loads(Path(cfg['sources']['panel']['path']).read_text())
 boxes=[]
 for box in panel['boxes']:
  choices=[]
  for slot in range(4):
   choices.append([{'point':tuple(xy),'code':choice['code'],'columns':choice['columns']}
    for choice in box['choices'][slot] for xy in choice['signed_points']])
  boxes.append({'kind':box['kind'],'choices':choices,'target':tuple(box['target_point'])})
f=fixed.f;e=fixed.e
field_inverse_calls=[0]
raw_inverse=f.inverse
def counted_inverse(value):
 field_inverse_calls[0]+=1
 return raw_inverse(value)
f.inverse=counted_inverse

def batch_inverse(words):
 """Return inverses of nonzero field elements with one EEA inversion."""
 if not words:return []
 prefix=[1]
 for w in words:
  assert w
  prefix.append(f.mul(prefix[-1],w))
 inv=f.inverse(prefix[-1]);out=[0]*len(words)
 for j in range(len(words)-1,-1,-1):
  out[j]=f.mul(inv,prefix[j])
  inv=f.mul(inv,words[j])
 assert inv==1
 return out

def batched_add_x(left,right):
 """Compute only x(left + right), with shared denominator inversion."""
 assert len(left)==len(right)
 out=[None]*len(left);denoms=[];ordinary=[]
 for j,(p,q) in enumerate(zip(left,right)):
  if p is None:
   out[j]=None if q is None else q[0]
  elif q is None:out[j]=p[0]
  elif p[0]==q[0]:
   out[j]=e.add(p,q)[0] if e.add(p,q) is not None else None
  else:
   ordinary.append(j);denoms.append(p[0]^q[0])
 invs=batch_inverse(denoms)
 for j,inv in zip(ordinary,invs):
  x,y=left[j];u,v=right[j]
  lam=f.mul(y^v,inv)
  out[j]=f.square(lam)^lam^x^u
 return out

rows=[];equiv=Counter();stage=Counter();statuses=[];hits=[]
for bi,box in enumerate(boxes):
 t=time.monotonic();choices=box['choices'];target=box['target']
 assert e.on_curve(target)
 left=[e.add(choices[0][i]['point'],choices[1][j]['point']) for i,j in itertools.product(range(4),repeat=2)]
 right=[e.add(choices[2][i]['point'],choices[3][j]['point']) for i,j in itertools.product(range(4),repeat=2)]
 left_target=[e.sub(target,p) for p in left]
 query_left=[];query_right=[];ids_all=[]
 for ids in itertools.product(range(4),repeat=4):
  lid=4*ids[0]+ids[1];rid=4*ids[2]+ids[3]
  query_left.append(left_target[lid]);query_right.append(e.neg(right[rid]));ids_all.append(ids)
 x0=batched_add_x(query_left,query_right)
 xbase=[None if x is None else f.frob(x,(fixed.n-rotation)%fixed.n) for x in x0]
 nz=[i for i,x in enumerate(xbase) if x]
 invs=batch_inverse([xbase[i] for i in nz])
 inverse={i:v for i,v in zip(nz,invs)}
 counts=Counter();box_hits=[]
 for j,ids in enumerate(ids_all):
  if x0[j] is None:status='IDENTITY_RESIDUAL';found=None
  elif x0[j]==0:status='ZERO_X_RESIDUAL';found=None
  else:
   p=f.mul(fixed.H,xbase[j])^f.mul(fixed.C,inverse[j])
   code=fixed.code_of_product(p)
   if code is None:status='OUTSIDE_PRODUCT_SUBSPACE';found=None
   else:
    a=fixed.source_a(code)
    assert fixed.source_product(code)==p
    if not fixed.source_valid(a):status='INELIGIBLE_CODE';found=None
    else:
     residual=e.add(query_left[j],query_right[j])
     assert residual is not None and residual[0]==x0[j]
     found=fixed.recover(residual,rotation)
     status=found['status']
     if status=='VERIFIED_PAIR_OUTPUT':
      selected=[choices[k][ids[k]] for k in range(4)]
      cols=[col for c in selected for col in c['columns']]+found['columns']
      if len(set(cols))<10 or code in [c['code'] for c in selected]:
       counts['COLUMN_OR_CODE_COLLISION']+=1
      else:
       assert e.add(e.sub(target,residual),residual)==target
       box_hits.append({'prefix_choice_indices':list(ids),'last_code':code,'factor_columns':cols,
        'residual_point':list(residual)})
  counts[status]+=1
 rows.append({'box_index':bi,'kind':box['kind'],'status_counts':dict(sorted(counts.items())),
  'verified_relations':box_hits,'box_seconds':time.monotonic()-t})
 hits.extend(box_hits)
 if resource.getrusage(resource.RUSAGE_SELF).ru_maxrss>cfg['rss_cap_bytes']:
  raise MemoryError('rss cap')
signal.alarm(0)
prior=json.loads((ROOT/(case+'_result.json')).read_text())
assert [r['status_counts'] for r in rows]==[r['status_counts'] for r in prior['rows']]
assert [r['verified_relations'][0]['last_code'] if r['verified_relations'] else None for r in rows]==[
 r['verified_relations'][0]['last_code'] if r['verified_relations'] else None for r in prior['rows']]
result={'status':'COMPLETE_BATCH_OUTPUT_FAST','candidate_id':None,'case':case,
 'curve_id':cfg['curve_id'],'boxes_completed':len(rows),'residuals_checked':sum(sum(r['status_counts'].values()) for r in rows),
 'rows':rows,'wall_seconds':time.monotonic()-start,
 'peak_rss_raw':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
 'field_inverse_calls':field_inverse_calls[0],
 'protocol_sha256':sha(HERE/(case+'_fast_protocol.json')),'script_sha256':sha(Path(__file__))}
(HERE/(case+'_fast_result.json')).write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
print(json.dumps({'case':case,'status':result['status'],'wall_seconds':result['wall_seconds'],
 'residuals_checked':result['residuals_checked'],'verified_relations':len(hits)},sort_keys=True))
