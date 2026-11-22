"""Exact shared-target public relation population and reference distribution."""
from collections import Counter
from fractions import Fraction
from pathlib import Path
import gzip,hashlib,itertools,json,time
H=Path(__file__).resolve().parent
P=json.loads((H/'protocol.json').read_text())
start=time.monotonic()

def selected(offsets,w):
    out=[]
    for t1,t2 in itertools.permutations(offsets,2):
        if w!=t1 and w!=t2:out.append((t1,t2))
        if len(out)==16:break
    assert len(out)==16
    return out

def hit_count(q,w):
    n=0
    for t1,t2 in selected(P['offsets'],w):
        for a,b in P['vectors']:
            n+=int(((a+b)*w-a*t1-b*t2)%q==0)
    return n

def read(source,info):
    blob=(source/info['path']).read_bytes()
    assert len(blob)==info['gzip_bytes'] and hashlib.sha256(blob).hexdigest()==info['gzip_sha256']
    raw=gzip.decompress(blob)
    assert hashlib.sha256(raw).hexdigest()==info['raw_sha256']
    rows=[json.loads(line) for line in raw.splitlines()]
    assert len(rows)==info['rows']
    return rows

population=[]; histograms={}
for spec in P['fields']:
    q=spec['q'];p=spec['p']
    assert all((a+b)%q!=0 and b%q!=0 for a,b in P['vectors'])
    rows=[{'p':p,'q':q,'w':w,'hits':hit_count(q,w)} for w in range(1,q)]
    population.extend(rows)
    histograms[str(p)]={str(k):v for k,v in sorted(Counter(x['hits'] for x in rows).items())}
    assert sum(histograms[str(p)].values())==q-1
    if time.monotonic()-start>P['resource_cap_seconds']:raise TimeoutError('population cap')

def conv(a,b):
    z=Counter()
    for x,n in a.items():
        for y,m in b.items():z[x+y]+=n*m
    return z

poly=Counter({0:1});denom=1
for spec in P['fields']:
    h=Counter({int(k):v for k,v in histograms[str(spec['p'])].items()})
    for _ in range(4):poly=conv(poly,h);denom*=spec['q']-1
assert sum(poly.values())==denom
observed=[]
for panel in P['source_panels']:
    path=(H/panel['result_path']).resolve();source=path.parent
    blob=path.read_bytes()
    assert hashlib.sha256(blob).hexdigest()==panel['result_sha256']
    result=json.loads(blob)
    files=result.get('files',result)
    queries=read(source,files['queries']);vectors=read(source,files['vectors'])
    assert len(queries)==512 and len(vectors)==6656
    per_field=[];total=0
    for fi,spec in enumerate(P['fields']):
        field_hits=0
        for j in range(4):
            w=1+int.from_bytes(hashlib.sha256(f"{panel['target_label']}|{spec['p']}|{j}".encode()).digest(),'big')%(spec['q']-1)
            pairs=selected(P['offsets'],w)
            event=fi*64+j*16
            for qi,(t1,t2) in enumerate(pairs):
                qr=queries[event+qi]
                assert (qr['event_index'],qr['p'],qr['q'],qr['w'],qr['target_index'],qr['query_index'],qr['t1'],qr['t2'])==(event+qi,spec['p'],spec['q'],w,j,qi,t1,t2)
                for vi,(a,b) in enumerate(P['vectors']):
                    vr=vectors[(event+qi)*13+vi]
                    yes=((a+b)*w-a*t1-b*t2)%spec['q']==0
                    assert (vr['event_index'],vr['vector_index'],vr['a'],vr['b'],vr['public_relation'])==(event+qi,vi,a,b,yes)
                    field_hits+=int(yes)
            assert hit_count(spec['q'],w)==sum(int(vectors[(event+qi)*13+vi]['public_relation']) for qi in range(16) for vi in range(13))
        per_field.append({'p':spec['p'],'hits':field_hits})
        total+=field_hits
    assert total==result['counts']['public_hits']
    observed.append({'panel':panel['name'],'total_hits':total,'per_field':per_field,'lower_tail_num':sum(n for x,n in poly.items() if x<=total),'upper_tail_num':sum(n for x,n in poly.items() if x>=total),'tail_denominator':denom})
raw=(''.join(json.dumps(x,sort_keys=True,separators=(',',':'))+'\n' for x in population)).encode()
packed=gzip.compress(raw,compresslevel=9,mtime=0)
(H/'population.jsonl.gz').write_bytes(packed)
files={'path':'population.jsonl.gz','rows':len(population),'gzip_bytes':len(packed),'gzip_sha256':hashlib.sha256(packed).hexdigest(),'raw_sha256':hashlib.sha256(raw).hexdigest()}
expectation=sum(x*n for x,n in poly.items())
result={'schema':'xedni-shared-target-hit-law-result-v1','status':'complete','protocol_sha256':hashlib.sha256((H/'protocol.json').read_bytes()).hexdigest(),'population_file':files,'per_field_histogram':histograms,'total_histogram':{str(k):v for k,v in sorted(poly.items())},'reference_denominator':denom,'expectation_numerator':expectation,'observed':observed,'elapsed_wall_seconds':round(time.monotonic()-start,3)}
(H/'result.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
print(json.dumps({'population_rows':len(population),'expected_hits':str(Fraction(expectation,denom)),'observed':[{k:v for k,v in row.items() if k in ('panel','total_hits')} for row in observed],'elapsed_wall_seconds':result['elapsed_wall_seconds']},indent=2))
