import json,sys,itertools,numpy as np
from collections import Counter
rng=np.random.default_rng(291161)
masks=np.array([sum(1<<b for b in bits) for bits in itertools.combinations(range(31),4)],dtype=np.uint32)
def count(x,y):
 a=masks
 for d in (x[y,None]^x[None,~y]).flatten():
  a=a[(a&d)!=0]
  if not len(a):break
 return len(a)
h=[Counter(),Counter()];paired=Counter()
for line in sys.stdin:
 v=np.array(json.loads(line),dtype=np.uint32); x=v[:,0]; y=v[:,1].astype(bool)
 assert len(x)==32 and len(set(x))==32 and y.sum()==17
 a,b=count(x,y),count(x,rng.permutation(y));h[0][a]+=1;h[1][b]+=1;paired[(bool(a),bool(b))]+=1
assert sum(h[0].values())==256
print(h,paired)
