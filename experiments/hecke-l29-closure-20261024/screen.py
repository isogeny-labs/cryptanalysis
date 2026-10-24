"""Find degree-29 fibers that could connect to the two newly introduced orbit columns."""
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
def key(P):return (-1,-1) if P.is_zero() else (int(P[0]),int(P[1]))

def main():
    path=HERE/'protocol.json';raw=path.read_bytes()
    protocol=json.loads(raw);assert protocol['status']=='FROZEN_BEFORE_L29_CLOSURE_SCREEN'
    source_path=ROOT/'hecke-higher-degree-screen-20261024/result.json'
    l29_path=ROOT/'hecke-degree-next-screen-20261024/l29_result.json'
    source=json.loads(source_path.read_text());l29=json.loads(l29_path.read_text())
    reps=[tuple(x) for x in l29['new_representatives']]
    assert reps==[tuple(x) for x in protocol['new_orbit_representatives']]
    funcs,jfun=H.build([2,3]);rd=H.Reduced(20023,funcs,jfun,[2,3])
    T=rd.E([5,5,1]);assert 5*T==rd.E(0)
    source_js=defaultdict(list)
    for rec in source['records']:
        source_js[rec['j']].extend(rec['source_points'])
    old_source_j_count=len(source_js)
    new_points=[];target_js=defaultdict(list)
    for rep in reps:
        P0=rd.E([*rep,1])
        for k in range(5):
            P=P0+k*T;j=rd.j(P)
            record={'representative':rep,'translate':k,'point':key(P),
                    'j':None if j is None else int(j)}
            new_points.append(record)
            if j is not None:
                source_js[int(j)].append(key(P))
                target_js[int(j)].append(record)
    F=GF(20023);R=PolynomialRing(F,'Y');Y=R.gen()
    phi=classical_modular_polynomial(29)
    adjacent=defaultdict(set);reverse_counts={}
    for tj in target_js:
        roots=R(phi(F(tj),Y)).roots()
        reverse_counts[tj]=sum(int(m) for _,m in roots)
        for sj,_ in roots:
            if int(sj) in source_js:adjacent[int(sj)].add(tj)
    # New sources are included even if their modular fibers are not self-adjacent.
    new_source_js={r['j'] for r in new_points if r['j'] is not None}
    candidates=sorted(set(adjacent)|new_source_js)
    rows=[]
    for sj in candidates:
        roots=R(phi(F(sj),Y)).roots()
        mult=sum(int(m) for _,m in roots)
        assert adjacent[sj]<={int(x) for x,_ in roots}
        rows.append({'source_j':sj,'source_points':source_js[sj],
                     'is_new_source_j':sj in new_source_js,
                     'linked_new_target_js':sorted(adjacent[sj]),
                     'rational_root_multiplicity':mult,
                     'distinct_rational_roots':len(roots),'fully_split':mult==30})
    out={'status':'L29_NEW_COLUMN_CLOSURE_SCREEN_PRODUCED',
         'protocol_sha256':sha(path),
         'source_sha256':{'old_source':sha(source_path),'l29':sha(l29_path)},
         'old_source_j_count':old_source_j_count,'new_points':new_points,
         'new_target_js':{str(j):v for j,v in target_js.items()},
         'reverse_root_counts':reverse_counts,
         'candidate_source_j_count':len(rows),'candidate_rows':rows,
         'fully_split_candidates':[r for r in rows if r['fully_split']],
         'candidate_id':None,'timing_claim':None}
    (HERE/'screen_result.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'new_target_j_count':len(target_js),'candidate_source_j_count':len(rows),
                      'fully_split_source_j_count':len(out['fully_split_candidates'])},sort_keys=True))

if __name__=='__main__':main()
