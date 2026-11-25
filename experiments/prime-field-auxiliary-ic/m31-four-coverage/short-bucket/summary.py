import csv,sys
from statistics import median
from collections import defaultdict
g=defaultdict(list)
for seed,r,a,b,p in csv.reader(open(sys.argv[1])):
    if int(r)>=0:g[int(a),seed].append((float(b),float(p)))
v={a:[median(sum(t) for t in g[a,s]) for s in sorted({s for k,s in g if k==a})] for a in sorted({a for a,s in g})}
for a,ts in v.items():
    print(a,'ms',median(ts)/1e6,'ns/query',median(median(t[1] for t in rows)/673130 for (k,s),rows in g.items() if k==a),'relative',min(x/y for x,y in zip(v[0],ts)),max(x/y for x,y in zip(v[0],ts)),file=sys.stderr)
print(min(v,key=lambda a:median(v[a])))
