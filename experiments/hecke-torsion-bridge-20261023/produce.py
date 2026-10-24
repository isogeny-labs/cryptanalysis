"""One-layer 5-torsion Hecke bridge and induced old-class rank gate."""
from collections import Counter,defaultdict
from hashlib import sha256
import json
from pathlib import Path
import sys
import time

from sage.all import (EllipticCurve_from_j, GF, QQ, classical_modular_polynomial,
                      matrix)

HERE=Path(__file__).resolve().parent
SOURCE=HERE.parent/'hecke-inert2-non3-cycle-20261023'/'full_matrix.json'
MODULE=HERE.parent/'hecke-two-sheet-small-order-20261023'/'tools'/'hecke11.py'
sys.path.insert(0,str(MODULE.parent))
import hecke11 as H

def sha(path):return sha256(path.read_bytes()).hexdigest()

def point_key(P):
    return (-1,-1) if P.is_zero() else (int(P[0]),int(P[1]))

def main():
    raw=(HERE/'protocol.json').read_bytes();protocol=json.loads(raw)
    assert protocol['status']=='FROZEN_BEFORE_TORSION_BRIDGE_PRODUCER'
    assert protocol['source_sha256']=={'matrix':sha(SOURCE),'hecke11':sha(MODULE),
                                       'producer':sha(HERE/'produce.py')}
    data=json.loads(SOURCE.read_text())
    assert data['status']=='NON3_CYCLE_FULL_MATRIX_PRODUCED'
    assert (data['d'],data['p'],data['f'],data['u_abs'])==(227,12043,6,200)
    funcs,jfun=H.build([2,3]);rd=H.Reduced(12043,funcs,jfun,[2,3])
    assert int(rd.E.order())==data['x0_11_group_order']==11960
    T=rd.E([5,5,1]);assert not T.is_zero() and 5*T==rd.E(0)
    assert point_key(T)==(5,5)
    pts=[rd.E([r['point'][0],r['point'][1],1]) for r in data['column_points']]
    assert len(set(pts))==120
    def orbit(P):return min(point_key(P+k*T) for k in range(5))
    representatives={orbit(P):min((P+k*T for k in range(5)),key=point_key)
                     for P in pts}
    old_keys={orbit(P) for P in pts}
    sources=defaultdict(list)
    for i,P in enumerate(pts):
        for k in (1,4):sources[P+k*T].append((i,k))
    new_sources=sorted((P for P in sources if P not in set(pts)),key=point_key)
    source_records=[];accepted=[];statuses=Counter();cross_class_rows=0
    phi={l:classical_modular_polynomial(l) for l in (2,3)}
    for P in new_sources:
        js=rd.j(P)
        if js is None:
            source_records.append({'point':point_key(P),'origin':sources[P],
                                   'status':'CUSP_OR_UNDEFINED_J'})
            statuses['CUSP_OR_UNDEFINED_J']+=1;continue
        trace_abs=abs(int(EllipticCurve_from_j(js).trace_of_frobenius()))
        source_records.append({'point':point_key(P),'origin':sources[P],
                               'status':'CLASSIFIED','j':int(js),'trace_abs':trace_abs})
        for l in (2,3):
            roots=rd.neighbour_x(l,P).roots()
            rational_roots=sum(int(m) for _,m in roots)
            if rational_roots!=l+1:
                statuses[f'L{l}_NOT_ALL_RATIONAL']+=1;continue
            nb=rd.neighbours_all(l,P)
            if nb is None or len(nb)!=l+1:
                statuses[f'L{l}_UNRESOLVED_NEIGHBOURS']+=1;continue
            if any(rd.j(Q) is None for Q in nb):
                statuses[f'L{l}_CUSP_NEIGHBOUR']+=1;continue
            assert sum(nb,rd.E(0))==rd.a_l[l]*P
            assert all(phi[l](js,rd.j(Q))==0 for Q in nb)
            coefficients=Counter(orbit(Q) for Q in nb)
            coefficients[orbit(P)]-=rd.a_l[l]
            coefficients={key:value for key,value in coefficients.items() if value}
            assert all(key in representatives or key==orbit(P) or any(key==orbit(Q) for Q in nb)
                       for key in coefficients)
            accepted.append({'source':point_key(P),'origin':sources[P],
                             'source_trace_abs':trace_abs,'degree':l,
                             'neighbours':[point_key(Q) for Q in nb],
                             'coefficients':coefficients})
            statuses[f'L{l}_ACCEPTED']+=1
            if trace_abs!=200:cross_class_rows+=1
    base_rows=[]
    for row in data['relation_rows']:
        coefficients=Counter()
        for col,value in row.items():coefficients[orbit(pts[int(col)])]+=int(value)
        base_rows.append({key:v for key,v in coefficients.items() if v})
    all_keys=sorted(old_keys|{key for row in accepted for key in row['coefficients']})
    old_cols=[key for key in all_keys if key in old_keys]
    new_cols=[key for key in all_keys if key not in old_keys]
    new_rows=[row['coefficients'] for row in accepted]
    full_rows=base_rows+new_rows
    rank_results={}
    for modulus in (101,1000000007):
        F=GF(modulus)
        def rank(rows,columns):
            return int(matrix(F,[[row.get(key,0) for key in columns] for row in rows],sparse=True).rank())
        start=time.monotonic()
        base=rank(base_rows,old_cols)
        full=rank(full_rows,all_keys)
        new_projection=rank(full_rows,new_cols) if new_cols else 0
        induced=full-new_projection
        rank_results[str(modulus)]={'baseline_old_rank':base,'full_rank':full,
                                    'new_column_projection_rank':new_projection,
                                    'induced_old_rank':induced,
                                    'induced_increment':induced-base,
                                    'rank_wall_s':time.monotonic()-start}
    def encode(row):return {str(all_keys.index(key)):int(v) for key,v in sorted(row.items())}
    out={'status':'TORSION_BRIDGE_ONE_LAYER_PRODUCED',
         'protocol_sha256':sha256(raw).hexdigest(),'script_sha256':sha(HERE/'produce.py'),
         'hecke11_sha256':sha(MODULE),'source_matrix_sha256':sha(SOURCE),
         'p':12043,'group_order':11960,'torsion_point':point_key(T),
         'base_point_count':len(pts),'old_orbit_count':len(old_keys),
         'translated_new_source_count':len(new_sources),'source_records':source_records,
         'accepted_rows':[{**{k:v for k,v in row.items() if k!='coefficients'},
                           'coefficients':encode(row['coefficients'])} for row in accepted],
         'base_rows':[encode(row) for row in base_rows],
         'column_representatives':all_keys,'old_column_indices':[all_keys.index(k) for k in old_cols],
         'new_column_indices':[all_keys.index(k) for k in new_cols],
         'status_counts':dict(statuses),'cross_class_accepted_rows':cross_class_rows,
         'rank_results':rank_results,'candidate_id':None,'timing_claim':None}
    (HERE/'result.json').write_text(json.dumps(out,sort_keys=True,indent=2)+'\n')
    print(json.dumps({'status':out['status'],'new_sources':len(new_sources),
                      'accepted_rows':len(accepted),'cross_class_rows':cross_class_rows,
                      'old_columns':len(old_cols),'new_columns':len(new_cols),
                      'rank_results':rank_results},sort_keys=True))

if __name__=='__main__':main()
