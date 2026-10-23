"""Audit the frozen D1407 walk while retaining its exceptional CM fiber."""
from collections import Counter
from hashlib import sha256
from pathlib import Path
import json
import sys

from sage.all import EllipticCurve_from_j, PolynomialRing, QQ, classical_modular_polynomial, matrix

P = Path(__file__).resolve().parent
sys.path.insert(0, str(P / 'tools'))
import hecke11 as H

def point(E, encoded):
    x, y = encoded[1:-1].split(' : ')[:2]
    return E([int(x), int(y), 1])

def rank(rows, modulus=None):
    if modulus is None:
        return int(matrix(QQ, [[int(row.get(str(i), 0)) for i in range(383)] for row in rows]).rank())
    pivots = {}
    for source in rows:
        row = {int(k): int(v)%modulus for k,v in source.items() if int(v)%modulus}
        while row:
            j = min(row)
            if j not in pivots:
                inv = pow(row[j], -1, modulus)
                pivots[j] = {k:v*inv%modulus for k,v in row.items()}
                break
            a = row[j]
            for k,v in pivots[j].items():
                new = (row.get(k,0)-a*v)%modulus
                if new: row[k]=new
                else: row.pop(k,None)
    return len(pivots)

def main():
    source = P/'data/exp11_class_walk_D1407_f6.json'
    saved = json.loads(source.read_text())
    receipt = json.loads((P/'launch.json').read_text())
    fibers = json.loads((P/'cm_fibers.json').read_text())
    assert receipt['result_sha256'] == sha256(source.read_bytes()).hexdigest()
    assert fibers['complete_count'] == fibers['saved_count'] == 383
    assert not fibers['missing_from_walk'] and not fibers['outside_four_strata']
    funcs,jfun = H.build([2,3]); rd = H.Reduced(12763,funcs,jfun,[2,3])
    points = [point(rd.E,s) for s in saved['column_points']]
    assert len(points) == len(set(points)) == 383
    idx={q:i for i,q in enumerate(points)}
    ring=PolynomialRing(rd.Fp,'J'); J=ring.gen()
    phi={ell:classical_modular_polynomial(ell) for ell in (2,3)}
    conductors={}; strata=Counter(); rows=[]; missing=[]; exceptions=[]; root_counts={2:Counter(),3:Counter()}
    for i,q in enumerate(points):
        j=rd.j(q)
        assert j is not None
        key=int(j)
        if key not in conductors:
            conductors[key]=int(EllipticCurve_from_j(j).endomorphism_order().conductor())
        c=conductors[key]
        assert c in (1,2,3,6)
        strata[c]+=1
        for ell in (2,3):
            predicted=ell+1 if (6//c)%ell==0 else 1
            hecke=rd.neighbour_x(ell,q).roots()
            modular=ring(phi[ell](j,J)).roots()
            hcount=sum(int(m) for _,m in hecke)
            mcount=sum(int(m) for _,m in modular)
            root_counts[ell][hcount]+=1
            if hcount!=predicted or mcount!=predicted:
                exceptions.append({'column':i,'degree':ell,'conductor':c,'predicted':predicted,'hecke':hcount,'modular':mcount})
            if predicted!=ell+1:continue
            neighbors=rd.neighbours_all(ell,q)
            if neighbors is None or len(neighbors)!=ell+1:
                exceptions.append({'column':i,'degree':ell,'conductor':c,'reason':'unreconstructed_full_neighbors'})
                continue
            assert sum(neighbors,rd.E(0))==rd.a_l[ell]*q
            outside=[str(n) for n in neighbors if n not in idx]
            if outside:
                missing.append({'column':i,'degree':ell,'conductor':c,'outside':outside})
                continue
            row=Counter(idx[n] for n in neighbors);row[i]-=rd.a_l[ell]
            decoded={str(k):int(v) for k,v in row.items() if v}
            expected={k:int(v) for k,v in saved['relation_rows'][len(rows)].items() if v}
            assert decoded==expected,(i,ell,len(rows))
            rows.append({'source_column':i,'source_conductor':c,'degree':ell})
    assert len(rows)==len(saved['relation_rows'])==286
    floor={i for i,q in enumerate(points) if conductors[int(rd.j(q))]==6}
    nonfloor=set(range(383))-floor
    ranks={}
    for modulus in (None,23,1000000007,2147483647):
        key='QQ' if modulus is None else str(modulus)
        ranks[key]={}
        for degrees in ((2,),(3,),(2,3)):
            selected=[row for row,meta in zip(saved['relation_rows'],rows) if meta['degree'] in degrees]
            projected=[{k:v for k,v in row.items() if int(k) in nonfloor} for row in selected]
            ranks[key]['+'.join(map(str,degrees))]=[rank(selected,modulus),rank(projected,modulus)]
    assert all(v['2+3'][0]==saved['rank'] for v in ranks.values())
    result={'status':'VERIFIED_D1407_EXCEPTIONAL_FIBER_MATRIX',
            'source_sha256':sha256(source.read_bytes()).hexdigest(),
            'script_sha256':sha256((P/'audit_exception.py').read_bytes()).hexdigest(),
            'conductor_counts':dict(strata),'root_counts':{str(k):dict(v) for k,v in root_counts.items()},
            'root_count_exceptions':exceptions,'rows_with_outside_neighbor':missing,
            'row_records':rows,'floor_columns':len(floor),
            'floor_column_indices':sorted(floor),
            'point_records':[{'column':i,'j':int(rd.j(q)),
                              'endomorphism_conductor':conductors[int(rd.j(q))]}
                             for i,q in enumerate(points)],
            'ranks':ranks,
            'candidate_id':None,'timing_claim':None}
    (P/'audit_exception.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'status':result['status'],'conductor_counts':result['conductor_counts'],
                      'root_count_exceptions':exceptions,'rows_with_outside_neighbor':missing,
                      'ranks_QQ':ranks['QQ']}))

if __name__=='__main__':main()
