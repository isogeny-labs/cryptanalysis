import gzip,json,random,math,collections,pathlib
P=pathlib.Path(__file__).parent
sums=collections.defaultdict(lambda:[0,0])
for arm,ix in (('main',1),('c12',0)):
 with gzip.open(P/f'rows_{arm}.jsonl.gz','rt') as f:
  for line in f:
   z=json.loads(line)
   if z['bits'] in (28,30,32,34): sums[(z['family'],z['bits'],z['curve'])][ix]+=z['ops']
rng=random.Random(20261107)
out={}
for family in ('j1728','j0'):
 arr=[[sums[(family,b,c)] for c in range(200)] for b in (28,30,32,34)]
 boots=[]
 for _ in range(10000):
  lr=0.0
  for cell in arr:
   a=t=0
   for _ in range(200):
    v=cell[rng.randrange(200)]; a+=v[0]; t+=v[1]
   lr+=math.log(a/t)
  boots.append(math.exp(lr/4))
 boots.sort()
 out[family]={'independent_seed':20261107,'replicates':10000,'percentile_1_25':boots[125],'percentile_98_75':boots[9875]}
(P/'independent-bootstrap.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out,indent=2))
