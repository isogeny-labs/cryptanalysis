"""Checked-Sage full conductor-stratified Hecke relation producer for D=-1199."""
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import sys

from sage.all import (EllipticCurve_from_j, PolynomialRing, QQ,
                      classical_modular_polynomial, hilbert_class_polynomial, matrix)

HERE = Path(__file__).resolve().parent
PREV = HERE.parent / 'hecke-ramified11-fiber-20261023'
SOURCE = HERE.parent / 'hecke-two-sheet-small-order-20261023'
sys.path.insert(0, str(SOURCE / 'tools'))
import hecke11 as H


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def main():
    protocol_raw = (HERE / 'protocol.json').read_bytes()
    protocol = json.loads(protocol_raw)
    assert protocol['status'] == 'FROZEN_BEFORE_FULL_PRODUCER'
    assert protocol['source_sha256']['hecke11'] == digest(SOURCE / 'tools/hecke11.py')
    assert protocol['source_sha256']['produce'] == digest(HERE / 'produce.py')
    assert protocol['source_sha256']['prior_walk'] == digest(PREV / 'walk.json')
    assert protocol['source_sha256']['prior_fiber'] == digest(PREV / 'fiber_gate_raw.json')
    p, d = protocol['p'], protocol['d']
    assert (p,d) == (10891,1199)
    funcs,jfun = H.build([2,3])
    rd = H.Reduced(p,funcs,jfun,[2,3])
    phi = {l: classical_modular_polynomial(l) for l in (2,3)}
    jr = PolynomialRing(rd.Fp,'J'); J = jr.gen()
    strata = {}
    point_records = []
    for c in (1,2,3,6):
        js = hilbert_class_polynomial(-d*c*c).change_ring(rd.Fp).roots(multiplicities=False)
        assert len(js) == protocol['class_numbers'][str(c)]
        pairs = []
        for j in js:
            model = EllipticCurve_from_j(j)
            assert abs(int(model.trace_of_frobenius())) == protocol['u_abs']
            assert int(model.endomorphism_order().conductor()) == c
            lifts = rd.points_with_j(j)
            assert len(lifts) == 1
            pairs.append((j,lifts[0]))
        pairs.sort(key=lambda jp:(int(jp[1][0]),int(jp[1][1])))
        strata[str(c)] = len(pairs)
        for j,q in pairs:
            point_records.append({'column':len(point_records),'conductor':c,'j':int(j),
                                  'point':[int(q[0]),int(q[1])]})
    assert strata == protocol['class_numbers']
    points = [rd.E([r['point'][0],r['point'][1],1]) for r in point_records]
    index = {q:i for i,q in enumerate(points)}
    assert len(points) == len(index) == 228
    rows = []; row_records = []; root_counts = {2:Counter(),3:Counter()}
    for i,q in enumerate(points):
        c = point_records[i]['conductor']; j = rd.j(q)
        assert int(j) == point_records[i]['j']
        for l in (2,3):
            expected = l+1 if (6//c)%l == 0 else 1
            got_x = sum(int(m) for _,m in rd.neighbour_x(l,q).roots())
            got_j = sum(int(m) for _,m in jr(phi[l](j,J)).roots())
            assert got_x == got_j == expected,(i,c,l,got_x,got_j)
            root_counts[l][expected] += 1
            if expected == 1: continue
            nb = rd.neighbours_all(l,q)
            assert nb is not None and len(nb) == l+1
            assert sum(nb,rd.E(0)) == rd.a_l[l]*q
            assert all(phi[l](j,rd.j(z)) == 0 for z in nb)
            assert all(z in index for z in nb)
            row = Counter(index[z] for z in nb)
            row[i] -= rd.a_l[l]
            rows.append({str(k):int(v) for k,v in sorted(row.items()) if v})
            row_records.append({'row':len(rows)-1,'source':i,'conductor':c,'degree':l})
    assert len(rows) == protocol['predicted_verified_rows']['total'] == 190
    by_degree = Counter(r['degree'] for r in row_records)
    assert dict(by_degree) == {2:114,3:76}
    nonfloor = {r['column'] for r in point_records if r['conductor'] != 6}
    c2_rows = {r['row'] for r in row_records if r['conductor'] == 2 and r['degree'] == 3}
    assert len(nonfloor) == 152 and len(c2_rows) == 38
    def rank(row_ids, cols):
        return int(matrix(QQ,[[rows[i].get(str(j),0) for j in cols] for i in row_ids]).rank())
    all_rows = list(range(len(rows))); all_cols = list(range(len(points)))
    nonfloor_cols = sorted(nonfloor)
    others = [i for i in all_rows if i not in c2_rows]
    ranks = {
        'full_QQ':rank(all_rows,all_cols),
        'nonfloor_QQ':rank(all_rows,nonfloor_cols),
        'without_c2_full_QQ':rank(others,all_cols),
        'without_c2_nonfloor_QQ':rank(others,nonfloor_cols),
        'c2_full_QQ':rank(sorted(c2_rows),all_cols),
        'c2_nonfloor_QQ':rank(sorted(c2_rows),nonfloor_cols),
    }
    ranks['floor_only_row_directions'] = ranks['full_QQ']-ranks['nonfloor_QQ']
    ranks['c2_increment_full_QQ'] = ranks['full_QQ']-ranks['without_c2_full_QQ']
    ranks['c2_increment_nonfloor_QQ'] = ranks['nonfloor_QQ']-ranks['without_c2_nonfloor_QQ']
    out = {'status':'FULL_D1199_RELATION_MATRIX_PRODUCED',
           'protocol_sha256':sha256(protocol_raw).hexdigest(),
           'source_sha256':digest(HERE/'produce.py'),
           'hecke11_sha256':digest(SOURCE/'tools/hecke11.py'),
           'p':p,'d':d,'f':6,'u_abs':protocol['u_abs'],
           'x0_11_model':[int(v) for v in H.AINV],
           'x0_11_group_order':int(rd.E.order()),
           'hecke_eigenvalues':{str(l):rd.a_l[l] for l in (2,3)},
           'stratum_points':strata,'column_points':point_records,
           'relation_rows':rows,'row_records':row_records,
           'row_counts_by_degree':{str(k):v for k,v in sorted(by_degree.items())},
           'rational_root_counts':{str(l):{str(k):v for k,v in sorted(ct.items())}
                                   for l,ct in root_counts.items()},
           'ranks':ranks,'candidate_id':None,'timing_claim':None}
    (HERE/'full_matrix.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'status':out['status'],'points':len(points),'rows':len(rows),
                      'strata':strata,'ranks':ranks},sort_keys=True))


if __name__ == '__main__':
    main()
