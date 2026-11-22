"""Independently replay an unpinned triple-plus-pair W11 public relation."""
import hashlib
import json
from pathlib import Path

from sage.all import EllipticCurve, GF, PolynomialRing

HERE=Path(__file__).resolve().parent
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def main():
    cfg=json.loads((HERE/'n41_audit_protocol.json').read_text())
    assert cfg['status']=='FROZEN_BEFORE_TRIPLE_PAIR_N41_RELATION_AUDIT'
    assert cfg['script_sha256']==sha(__file__)
    for rec in cfg['sources'].values():assert sha(rec['path'])==rec['sha256']
    P=PolynomialRing(GF(2),'u');u=P.gen()
    K=GF(2**41,name='u',modulus=u**41+u**3+1)
    E=EllipticCurve(K,[1,0,0,0,1])
    dec=lambda x:K(P([(int(x)>>i)&1 for i in range(41)]))
    enc=lambda x:sum(int(b)<<i for i,b in enumerate(x.polynomial().list()))
    rows=(HERE/'n41_join_input.tsv').read_text().splitlines()
    assert rows[0]=='W11FIVE 5 1124 1'
    states={};target=None
    for line in rows[1:]:
        a=line.split()
        if a[0]=='T':target=E(dec(a[2]),dec(a[3]))
        if a[0]=='S':
            slot,sid=map(int,a[1:3]);states[slot,sid]=a
    assert len(states)==5620 and target is not None
    for sid in range(1124):
        assert all(states[slot,sid][-2:]==states[0,sid][-2:] for slot in (0,1,2))
        assert all(states[slot,sid][-2:]==states[3,sid][-2:] for slot in (3,4))
    receipt=json.loads((HERE/'n41_join_result.json').read_text())
    assert receipt['status']=='COMPLETE_HIT'
    hit=receipt['hit'].split();assert hit[0]=='HIT' and len(hit)==11
    ids=list(map(int,hit[1:6]))
    columns=[];codes=[];points=[];leaves=[];rotated_leaves=[]
    rotations=[0,0,0,12,12]
    def rotate(point,k):return E(point[0]**(1<<k),point[1]**(1<<k))
    for slot,sid in enumerate(ids):
        row=states[slot,sid]
        code=int(row[3]);branch=int(row[4]);a,b=map(int,row[5:7])
        assert branch==sid%4 and b==a^112
        pa=E.lift_x(1+~(sum(dec(a)**(4**j) for j in range(21))),all=True)
        pb=E.lift_x(1+~(sum(dec(b)**(4**j) for j in range(21))),all=True)
        assert len(pa)==len(pb)==2
        pt=pa[branch//2]+pb[branch%2]
        pt=rotate(pt,rotations[slot])
        assert pt==E(dec(row[-2]),dec(row[-1]))
        ca,cb=int(row[7]),int(row[8])
        folded=lambda point:min(enc(point[0]**(1<<j)) for j in range(41))
        assert ca==folded(pa[branch//2]) and cb==folded(pb[branch%2])
        columns.extend([ca,cb])
        codes.append(code);points.append(pt);leaves.extend([pa[branch//2],pb[branch%2]])
        rotated_leaves.extend([rotate(pa[branch//2],rotations[slot]),
                              rotate(pb[branch%2],rotations[slot])])
    assert len(set(codes))==5 and len(set(columns))==10
    assert sum(points,E(0))==target
    assert 4*target!=E(0) and 549756390943*(4*target)==E(0)
    assert sum(rotated_leaves,E(0))==target
    ordered=sorted(zip(codes[:3],points[:3]),key=lambda item:item[0]) + \
            sorted(zip(codes[3:],points[3:]),key=lambda item:item[0])
    assert sum((point for _,point in ordered),E(0))==target
    result={'status':'PASS_TRIPLE_PAIR_N41_PUBLIC_RELATION','candidate_id':None,
            'curve_id':'EC1N41Ckb1h7d5e80d3c4d0','target':[enc(target[0]),enc(target[1])],
            'state_ids':ids,'codes':codes,'canonical_group_sorted_codes':[code for code,_ in ordered],
            'distinct_folded_columns':len(set(columns)),
            'native_probe':int(hit[6]),
            'raw_group_sum_verified':True,'subgroup_projection_verified':True,
            'protocol_sha256':sha(HERE/'n41_audit_protocol.json')}
    (HERE/'n41_audit_result.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
    print(json.dumps(result,sort_keys=True))

if __name__=='__main__':main()
