"""Checked-Sage non-three-cycle inert-2 X0(11) relation matrix."""
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import sys

from sage.all import (EllipticCurve_from_j, PolynomialRing, QQ,
                      classical_modular_polynomial, hilbert_class_polynomial, matrix)

HERE=Path(__file__).resolve().parent
SOURCE=HERE.parent/'hecke-two-sheet-small-order-20261023'
sys.path.insert(0,str(SOURCE/'tools'))
import hecke11 as H


def digest(path):return sha256(path.read_bytes()).hexdigest()


def main():
    raw=(HERE/'producer_protocol.json').read_bytes();protocol=json.loads(raw)
    assert protocol['status']=='FROZEN_BEFORE_NON3_CYCLE_MATRIX'
    for name,path in [('source',HERE/'produce.py'),('hecke11',SOURCE/'tools/hecke11.py'),
                      ('selection',HERE/'selection.json'),('gate',HERE/'fiber_gate.json')]:
        assert protocol['source_sha256'][name]==digest(path)
    assert (protocol['d'],protocol['p'],protocol['u_abs'])==(227,12043,200)
    funcs,jfun=H.build([2,3]);rd=H.Reduced(12043,funcs,jfun,[2,3])
    phi={l:classical_modular_polynomial(l) for l in (2,3)}
    jr=PolynomialRing(rd.Fp,'J');J=jr.gen()
    point_records=[]
    for c in (1,2,3,6):
        js=hilbert_class_polynomial(-227*c*c).change_ring(rd.Fp).roots(multiplicities=False)
        assert len(js)==protocol['class_numbers'][str(c)]
        pairs=[]
        for j in js:
            model=EllipticCurve_from_j(j)
            assert abs(int(model.trace_of_frobenius()))==200
            reported=int(model.endomorphism_order().conductor())
            assert reported==c,(c,int(j),reported)
            lifts=rd.points_with_j(j)
            assert len(lifts)==2
            pairs.extend((j,q) for q in lifts)
        pairs.sort(key=lambda jq:(int(jq[1][0]),int(jq[1][1])))
        assert len(pairs)==protocol['predicted_points_by_conductor'][str(c)]
        for j,q in pairs:
            point_records.append({'column':len(point_records),'conductor':c,'j':int(j),
                                  'point':[int(q[0]),int(q[1])]})
    assert len(point_records)==120
    points=[rd.E([r['point'][0],r['point'][1],1]) for r in point_records]
    index={q:i for i,q in enumerate(points)}
    assert len(index)==120
    rows=[];meta=[];root_counts={2:Counter(),3:Counter()}
    neighbours_by_source_degree={}
    for i,q in enumerate(points):
        c=point_records[i]['conductor'];j=rd.j(q)
        assert int(j)==point_records[i]['j']
        for l in (2,3):
            expected=l+1 if (6//c)%l==0 else 1
            got_x=sum(int(m) for _,m in rd.neighbour_x(l,q).roots())
            got_j=sum(int(m) for _,m in jr(phi[l](j,J)).roots())
            assert got_x==got_j==expected,(i,c,l,got_x,got_j)
            root_counts[l][expected]+=1
            if expected==1:continue
            nb=rd.neighbours_all(l,q)
            assert nb is not None and len(nb)==l+1
            assert sum(nb,rd.E(0))==rd.a_l[l]*q
            assert all(phi[l](j,rd.j(z))==0 for z in nb)
            assert all(z in index for z in nb)
            neighbour_ids=[index[z] for z in nb]
            neighbours_by_source_degree[(i,l)]=neighbour_ids
            row=Counter(neighbour_ids);row[i]-=rd.a_l[l]
            rows.append({str(k):int(v) for k,v in sorted(row.items()) if v})
            meta.append({'row':len(rows)-1,'source':i,'conductor':c,'degree':l})
    assert len(rows)==protocol['predicted_verified_rows']['total']==70
    counts=Counter((r['conductor'],r['degree']) for r in meta)
    assert counts=={(1,2):10,(1,3):10,(2,3):30,(3,2):20}
    c1=[r['column'] for r in point_records if r['conductor']==1]
    c2=[r['column'] for r in point_records if r['conductor']==2]
    c2_descendants=[]
    for source in c1:
        n2=neighbours_by_source_degree[(source,2)]
        assert len(n2)==3 and all(point_records[j]['conductor']==2 for j in n2)
        assert len(set(n2))==3
        c2_descendants.extend(n2)
    assert len(set(c2_descendants))==30 and set(c2_descendants)==set(c2)
    c2_rows=[r['row'] for r in meta if r['conductor']==2 and r['degree']==3]
    others=[i for i in range(70) if i not in c2_rows]
    nonfloor=[r['column'] for r in point_records if r['conductor']!=6]
    def rank(row_ids,cols):
        return int(matrix(QQ,[[rows[i].get(str(j),0) for j in cols] for i in row_ids]).rank())
    full_cols=list(range(120));all_rows=list(range(70))
    ranks={'full_QQ':rank(all_rows,full_cols),
           'nonfloor_QQ':rank(all_rows,nonfloor),
           'others_full_QQ':rank(others,full_cols),
           'others_nonfloor_QQ':rank(others,nonfloor),
           'c2_full_QQ':rank(c2_rows,full_cols),
           'c2_nonfloor_QQ':rank(c2_rows,nonfloor)}
    ranks['c2_increment_full_QQ']=ranks['full_QQ']-ranks['others_full_QQ']
    ranks['c2_increment_nonfloor_QQ']=ranks['nonfloor_QQ']-ranks['others_nonfloor_QQ']
    ranks['floor_only_row_directions']=ranks['full_QQ']-ranks['nonfloor_QQ']
    out={'status':'NON3_CYCLE_FULL_MATRIX_PRODUCED',
         'producer_protocol_sha256':sha256(raw).hexdigest(),
         'script_sha256':digest(HERE/'produce.py'),
         'hecke11_sha256':digest(SOURCE/'tools/hecke11.py'),
         'd':227,'p':12043,'f':6,'u_abs':200,
         'x0_11_model':[int(v) for v in H.AINV],
         'x0_11_group_order':int(rd.E.order()),
         'hecke_eigenvalues':{str(l):rd.a_l[l] for l in (2,3)},
         'column_points':point_records,'relation_rows':rows,'row_records':meta,
         'rational_root_counts':{str(l):{str(k):v for k,v in sorted(ct.items())}
                                 for l,ct in root_counts.items()},
         'c1_degree2_to_c2':{str(i):neighbours_by_source_degree[(i,2)] for i in c1},
         'ranks':ranks,'candidate_id':None,'timing_claim':None}
    (HERE/'full_matrix.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'status':out['status'],'points':len(points),'rows':len(rows),
                      'ranks':ranks},sort_keys=True))


if __name__=='__main__':main()
