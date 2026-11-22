"""Root-index replay of the full target-scalar population and reference law."""
from collections import Counter
from fractions import Fraction
from pathlib import Path
import gzip,hashlib,itertools,json
H=Path(__file__).resolve().parent
P=json.loads((H/'protocol.json').read_text());R=json.loads((H/'result.json').read_text())
assert hashlib.sha256((H/'protocol.json').read_bytes()).hexdigest()==R['protocol_sha256']
info=R['population_file'];blob=(H/info['path']).read_bytes()
assert len(blob)==info['gzip_bytes'] and hashlib.sha256(blob).hexdigest()==info['gzip_sha256']
raw=gzip.decompress(blob)
assert hashlib.sha256(raw).hexdigest()==info['raw_sha256']
rows=[json.loads(line) for line in raw.splitlines()]
assert len(rows)==info['rows']==sum(s['q']-1 for s in P['fields'])

def pairs(w):
    eligible=[(x,y) for x in P['offsets'] for y in P['offsets'] if x!=y and w not in (x,y)]
    return eligible[:16]

index=0;hs={};field_means=[]
for spec in P['fields']:
    q=spec['q'];p=spec['p']
    roots=Counter()
    for t1,t2 in itertools.permutations(P['offsets'],2):
        for a,b in P['vectors']:
            divisor=(a+b)%q
            assert divisor!=0
            w=((a*t1+b*t2)*pow(divisor,-1,q))%q
            if w!=0 and (t1,t2) in pairs(w):roots[w]+=1
    hist=Counter()
    for w in range(1,q):
        row=rows[index];index+=1
        assert row=={'p':p,'q':q,'w':w,'hits':roots[w]}
        hist[roots[w]]+=1
    assert {str(k):v for k,v in sorted(hist.items())}==R['per_field_histogram'][str(p)]
    hs[p]=hist
    field_means.append(Fraction(4*sum(k*n for k,n in hist.items()),q-1))
assert index==len(rows)
# Independent probability convolution using rational coefficients rather than
# the producer's integer numerator/denominator convolution.
dist={0:Fraction(1)}
for spec in P['fields']:
    h=hs[spec['p']];den=spec['q']-1
    for _ in range(4):
        nxt={}
        for x,px in dist.items():
            for y,n in h.items():nxt[x+y]=nxt.get(x+y,Fraction(0))+px*Fraction(n,den)
        dist=nxt
assert sum(dist.values())==1
assert dist=={int(k):Fraction(n,R['reference_denominator']) for k,n in R['total_histogram'].items()}
assert sum(field_means)==Fraction(R['expectation_numerator'],R['reference_denominator'])
for panel in P['source_panels']:
    source=(H/panel['result_path']).resolve()
    assert hashlib.sha256(source.read_bytes()).hexdigest()==panel['result_sha256']
    obs=next(x for x in R['observed'] if x['panel']==panel['name'])
    totals=[]
    for fi,spec in enumerate(P['fields']):
        p=spec['p'];q=spec['q']
        field=0
        for j in range(4):
            digest=hashlib.sha256(f"{panel['target_label']}|{p}|{j}".encode()).digest()
            w=1+int.from_bytes(digest,'big')%(q-1)
            field+=rows[sum(s['q']-1 for s in P['fields'][:fi])+w-1]['hits']
        totals.append(field)
    assert totals==[x['hits'] for x in obs['per_field']]
    t=sum(totals)
    assert t==obs['total_hits']==json.loads(source.read_text())['counts']['public_hits']
    assert sum(v for x,v in dist.items() if x<=t)==Fraction(obs['lower_tail_num'],obs['tail_denominator'])
    assert sum(v for x,v in dist.items() if x>=t)==Fraction(obs['upper_tail_num'],obs['tail_denominator'])
receipt={'schema':'xedni-shared-target-hit-law-audit-v1','status':'PASS',
         'population_rows':len(rows),'source_panels_checked':len(P['source_panels']),
         'result_sha256':hashlib.sha256((H/'result.json').read_bytes()).hexdigest()}
(H/'audit-result.json').write_text(json.dumps(receipt,sort_keys=True,indent=2)+'\n')
print(json.dumps(receipt,sort_keys=True,indent=2))
