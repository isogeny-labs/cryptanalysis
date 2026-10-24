"""Rebuild saved source j map and replay all closure-screen roots."""
from collections import defaultdict
from hashlib import sha256
import json
from pathlib import Path
import sys
from sage.all import GF, PolynomialRing, classical_modular_polynomial

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
sys.path.insert(0,str(ROOT/'hecke-two-sheet-small-order-20261023/tools'))
import hecke11 as H
def sha(p):return sha256(p.read_bytes()).hexdigest()
def key(P):return [-1,-1] if P.is_zero() else [int(P[0]),int(P[1])]

def main():
    protocol=json.loads((HERE/'validation_protocol.json').read_text())
    assert protocol['status']=='FROZEN_BEFORE_CLOSURE_VALIDATION'
    paths={'validator':HERE/'validate.py','screen':HERE/'screen_result.json',
           'old_source':ROOT/'hecke-higher-degree-screen-20261024/result.json',
           'frontier':ROOT/'hecke-torsion-frontiers-20261024/p20023.result.json',
           'l29':ROOT/'hecke-degree-next-screen-20261024/l29_result.json',
           'hecke11':ROOT/'hecke-two-sheet-small-order-20261023/tools/hecke11.py'}
    assert protocol['source_sha256']=={k:sha(v) for k,v in paths.items()}
    saved=json.loads(paths['screen'].read_text())
    old=json.loads(paths['frontier'].read_text())
    l29=json.loads(paths['l29'].read_text())
    funcs,jfun=H.build([2,3]);rd=H.Reduced(20023,funcs,jfun,[2,3])
    T=rd.E([5,5,1]);assert 5*T==rd.E(0)
    source_js=defaultdict(list)
    undefined=[]
    for rep in old['column_representatives']:
        P0=rd.E(0) if rep==[-1,-1] else rd.E([*rep,1])
        for k in range(5):
            P=P0+k*T;j=rd.j(P)
            if j is None:undefined.append(key(P))
            else:source_js[int(j)].append(key(P))
    assert len(undefined)==2 and len(source_js)==11619
    old_source=json.loads(paths['old_source'].read_text())
    assert {r['j']:sorted(map(tuple,r['source_points'])) for r in old_source['records']} == \
           {j:sorted(map(tuple,points)) for j,points in source_js.items()}
    new_points=[];targets=defaultdict(list)
    for rep in l29['new_representatives']:
        P0=rd.E([*rep,1])
        for k in range(5):
            P=P0+k*T;j=rd.j(P)
            record={'representative':rep,'translate':k,'point':key(P),
                    'j':None if j is None else int(j)}
            new_points.append(record)
            if j is not None:
                source_js[int(j)].append(key(P));targets[int(j)].append(record)
    assert new_points==saved['new_points']
    assert {str(j):v for j,v in targets.items()}==saved['new_target_js']
    F=GF(20023);R=PolynomialRing(F,'Z');Z=R.gen();phi=classical_modular_polynomial(29)
    adjacent=defaultdict(set);reverse_counts={}
    for tj in targets:
        roots=R(phi(F(tj),Z)).roots()
        reverse_counts[tj]=sum(int(m) for _,m in roots)
        for sj,_ in roots:
            if int(sj) in source_js:adjacent[int(sj)].add(tj)
    assert {int(j):v for j,v in saved['reverse_root_counts'].items()}==reverse_counts
    new_source_js={r['j'] for r in new_points if r['j'] is not None}
    assert {r['source_j'] for r in saved['candidate_rows']}==set(adjacent)|new_source_js
    for row in saved['candidate_rows']:
        sj=row['source_j'];roots=R(phi(F(sj),Z)).roots()
        assert row['source_points']==source_js[sj]
        assert row['linked_new_target_js']==sorted(adjacent[sj])
        assert adjacent[sj]<={int(x) for x,_ in roots}
        assert row['rational_root_multiplicity']==sum(int(m) for _,m in roots)
        assert row['distinct_rational_roots']==len(roots)
        assert row['fully_split']==(row['rational_root_multiplicity']==30)
    assert saved['fully_split_candidates']==[r for r in saved['candidate_rows'] if r['fully_split']]
    result={'status':'PASS_L29_NEW_COLUMN_CLOSURE_REPLAY',
            'old_source_points_reconstructed':19745,'new_source_points_reconstructed':10,
            'target_j_count':len(targets),'candidate_source_j_count':len(saved['candidate_rows']),
            'fully_split_source_j_count':len(saved['fully_split_candidates']),
            'fully_split_source_points':[r['source_points'] for r in saved['fully_split_candidates']],
            'source_sha256':{k:sha(v) for k,v in paths.items()}}
    (HERE/'validation.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps({k:result[k] for k in ('status','candidate_source_j_count','fully_split_source_j_count')},sort_keys=True))

if __name__=='__main__':main()
