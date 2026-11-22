"""Same counts: two ic bench reports agree on the instance, every integer
counter and the recovered logarithms (timings, calibration and rho excluded)."""
import json,sys
SKIP=('parallel','wall','ns','seconds','elapsed','bytes','calibration','software','markdown','gae','rho')
def leaves(o,path=''):
    if isinstance(o,dict):
        for k,v in o.items():
            if any(t in k for t in SKIP): continue
            yield from leaves(v,path+'/'+k)
    elif isinstance(o,list):
        for i,v in enumerate(o): yield from leaves(v,f'{path}[{i}]')
    elif isinstance(o,(int,str,bool)) or o is None:
        yield path,o
def load(f):
    d=json.load(open(f)); return dict(leaves({'instance':d.get('instance'),'rows':d['rows']}))
a,b=load(sys.argv[1]),load(sys.argv[2])
diff=[k for k in set(a)|set(b) if a.get(k)!=b.get(k)]
print('IDENTICAL' if not diff else 'DIFF', len(a), 'leaves', *sorted(diff)[:10])
