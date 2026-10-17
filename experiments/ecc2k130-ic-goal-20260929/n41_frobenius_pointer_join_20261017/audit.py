import json
from pathlib import Path
D=Path(__file__).resolve().parent
src=D.parent/'n41_sixpair_shared_target_20261017'/'join_input.tsv'
lines=src.read_text().splitlines()
h=lines[0].split(); assert h[:3]==['ECC2K41','6','160']; target=(int(h[3]),int(h[4]))
P=(1<<41)|(1<<3)|1;M=(1<<41)-1

def mul(a,b):
    z=0
    while b:
        if b&1:z^=a
        b>>=1;a<<=1
        if a&(1<<41):a^=P
    return z

def sq(a):return mul(a,a)
def frob(a):
    for _ in range(18):a=sq(a)
    return a

def inv(a):
    assert a
    r=1;b=a;e=(1<<41)-2
    while e:
        if e&1:r=mul(r,b)
        b=sq(b);e>>=1
    assert mul(r,a)==1
    return r

def add(p,q):
    if p is None:return q
    if q is None:return p
    x,y=p;u,v=q
    if x==u:
        if y!=v or x==0:return None
        s=x^mul(y,inv(x));xx=sq(s)^s;yy=sq(x)^mul(s^1,xx)
    else:
        s=mul(y^v,inv(x^u));xx=sq(s)^s^x^u;yy=mul(s,x^xx)^xx^y
    return xx,yy

rows={}
for line in lines[1:]:
    f=line.split();assert f[0]=='S'
    slot,idx=map(int,f[1:3]);rows[slot,idx]=(int(f[9]),int(f[10]),int(f[7]),int(f[8]))
assert len(rows)==960
for j in range(3):
    for idx in range(160):
        x,y,ca,cb=rows[j,idx];u,v,cc,cd=rows[j+3,idx]
        assert (frob(x),frob(y))==(u,v)
for j in range(3):
    k=(j+1)%3
    for a in range(160):
        x=rows[j,a];u=rows[j+3,a]
        for b in range(160):
            y=rows[k,b];v=rows[k+3,b]
            assert (len({x[2],x[3],y[2],y[3]})==4) == (len({u[2],u[3],v[2],v[3]})==4)
# Verify the hit and exact target equality independently of both join binaries.
ids=list(map(int,(D/'run_0_direct.stdout').read_text().splitlines()[-1].split()[1:7]))
assert ids==[12,122,116,47,128,34]
points=[];cols=[]
for j,idx in enumerate(ids):
    x,y,a,b=rows[j,idx];points.append((x,y));cols += [a,b]
assert len(set(cols))==12
left=add(add(points[0],points[1]),points[2]);right=add(add(points[3],points[4]),points[5])
template=[(rows[j,ids[j+3]][0],rows[j,ids[j+3]][1]) for j in range(3)]
template_sum=add(add(template[0],template[1]),template[2])
assert right==(frob(template_sum[0]),frob(template_sum[1]))
assert add(left,right)==target
for i,arm in enumerate(['direct','pointer','vector','vector','pointer','direct']):
    text=(D/f'run_{i}_{arm}.stdout').read_text().splitlines()
    assert len(text)==3
    assert text[1].split()[1]=='3750144'
    assert tuple(map(int,text[2].split()[1:9]))==tuple(ids+[1100323,3])
out={'status':'PASS','matched_runs':6,'left_triples_per_run':3750144,'probes_per_run':1100323,'state_frobenius_checks':480,'pair_compatibility_checks':3*160*160,
     'witness_ids':ids,'left_sum':left,'right_sum':right,'target':target,'distinct_columns':12}
(D/'audit_result.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
print(json.dumps(out))
