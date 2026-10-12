"""Independent source, group, quotient-row audit of the N41 all-seed hit."""
import hashlib,json
from pathlib import Path
from collections import defaultdict
from sage.all import EllipticCurve,GF,PolynomialRing,Zmod
h=Path(__file__).resolve().parent;root=h.parents[1]
base=root/'n41_w7_entropy_cubic_20261011/w8'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
ap=json.loads((h/'audit_protocol.json').read_text())
paths={'source':h/'audit_sage.py','receipt':h/'receipt.json','stdout':h/'stdout.log',
       'input':h/'pairs.tsv','geometry':base/'geometry.json','fixture':base/'fixture.json',
       'sage_runtime':h/'audit_sage_runtime_info.json'}
assert {k:sha(v) for k,v in paths.items()}==ap['sha256']
receipt=json.loads((h/'receipt.json').read_text())
assert receipt['status']=='HIT_PENDING_INDEPENDENT_REPLAY' and receipt['stop_reason'] is None
geo=json.loads((base/'geometry.json').read_text());fixture=json.loads((base/'fixture.json').read_text())
rows={int(r['mask']):r for r in geo['rows']}
ring=PolynomialRing(GF(2),'t');t=ring.gen();F=GF(2**41,name='t',modulus=t**41+t**3+1)
E=EllipticCurve(F,[1,0,0,0,1]);r=549756390943
def dec(n):return F(ring([(int(n)>>i)&1 for i in range(41)]))
def enc(v):return sum(int(b)<<i for i,b in enumerate(v.polynomial().list()))
def xy(P):return [enc(P[0]),enc(P[1])]
def frob(P,k):return E(P[0]**(1<<k),P[1]**(1<<k))
raw={m:E(*map(dec,row['raw_point'])) for m,row in rows.items()}
diagonal={m:raw[m]+frob(raw[m],1) for m in raw}
assert all(P!=E(0) and P[0]==1/dec(m<<1) for m,P in diagonal.items())
proj={m:4*P for m,P in raw.items()}
assert all(P!=E(0) and r*P==E(0) for P in proj.values())
source={};target={}
for line in (h/'pairs.tsv').read_text().splitlines()[1:]:
    v=line.split()
    if v[0]=='S':source[(int(v[1]),int(v[2]))]=list(map(int,v[3:]))
    elif v[0]=='T':target[int(v[1])]=[int(v[2]),int(v[3])]
assert len(source)==123808 and len(target)==4
assert [target[i] for i in range(4)]==fixture['raw_target_preimages']
hits=[line.split() for line in (h/'stdout.log').read_text().splitlines() if line.startswith('HIT ')]
assert len(hits)==1
v=hits[0];ti=int(v[1]);ids=list(map(int,v[2:6]));assert len(ids)==4
rotations=(0,7,14,21);selected=[];occupied=set();running=E(0);pairs=[]
for slot,sid in enumerate(ids):
    a,b,ca,cb,sa,sb,x,y=source[(slot,sid)]
    assert a<b and rows[a]['column']==ca and rows[b]['column']==cb
    assert ca!=cb and ca not in occupied and cb not in occupied
    occupied.update([ca,cb]);selected.extend([a,b])
    P=frob((-diagonal[a] if sa else diagonal[a])+(-diagonal[b] if sb else diagonal[b]),rotations[slot])
    assert xy(P)==[x,y]
    running+=P
    pairs.append({'slot':slot,'state_id':sid,'masks':[a,b],'columns':[ca,cb],
                  'sign_bits':[sa,sb],'rotation':rotations[slot],'point':[x,y]})
assert len(occupied)==8 and xy(running)==target[ti]
assert xy(4*running)==fixture['public_target_transported']
reps={}
for m,row in sorted(rows.items()):reps.setdefault(int(row['column']),m)
A=PolynomialRing(Zmod(r),'L');L=A.gen();roots=[int(x) for x,_ in (L**2+L+2).roots()]
sample=proj[reps[min(reps)]]
lam=[x for x in roots if x*sample==frob(sample,1)]
assert len(lam)==1;lam=lam[0]
coeff=defaultdict(int)
for P in pairs:
    for mask,sign in zip(P['masks'],P['sign_bits']):
        col=int(rows[mask]['column']);baseP=proj[reps[col]]
        choices=[]
        for k in range(41):
            Q=frob(baseP,k)
            if Q==proj[mask]:choices.append((k,1))
            if -Q==proj[mask]:choices.append((k,-1))
        assert len(choices)==1
        k,osign=choices[0]
        coeff[col]=(coeff[col]+(-1 if sign else 1)*osign*(1+lam)*pow(lam,P['rotation']+k,r))%r
assert all(coeff.values())
rowcheck=E(0)
for col,c in coeff.items():rowcheck+=c*proj[reps[col]]
assert rowcheck==4*running
prior=[]
for name in ['n41_w8_sixpair_mitm_20261011','n41_w8_ninepair_join_control_20261012','n41_w8_tenpair_xquotient_20261012']:
    old=json.loads((root/name/'audit_result.json').read_text())
    if 'relation_row' in old:
        rr=old['relation_row']
        if isinstance(rr,list):prior.append({int(z['column']):int(z['coefficient_mod_r']) for z in rr})
        else:prior.append({int(k):int(v) for k,v in rr.items()})
assert len(prior)==3
# Independent modular elimination for rank novelty.
def rank(matrix):
    piv={}
    for row in matrix:
        w={int(k):int(v)%r for k,v in row.items() if int(v)%r}
        while w:
            k=min(w)
            if k not in piv:
                z=pow(w[k],-1,r);piv[k]={j:(v*z)%r for j,v in w.items()};break
            fac=w[k];old=piv[k]
            for j,v in old.items():
                w[j]=(w.get(j,0)-fac*v)%r
                if not w[j]:w.pop(j,None)
    return len(piv)
oldrank=rank(prior);newrank=rank(prior+[coeff]);assert oldrank==3 and newrank==4
result={'status':'PASS_INDEPENDENT_N41_DIAGONAL_ALLSEED_FOURPAIR_RELATION','curve_id':'EC1N41Ckb1h7d5e80d3c4d0',
        'raw_preimage_index':ti,'raw_sum':xy(running),'public_target':xy(4*running),
        'pair_count':4,'distinct_folded_columns':len(occupied),'rank_with_prior_rows':newrank,
        'prior_rank':oldrank,'pairs':pairs,'relation_row':{str(k):str(v) for k,v in coeff.items()},
        'sha256':{k:sha(v) for k,v in paths.items()},'audit_protocol_sha256':sha(h/'audit_protocol.json')}
(h/'audit_result.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
print(result['status'],len(occupied),newrank)
