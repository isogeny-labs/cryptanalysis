"""Independent exact audit of the D=-2631 class, rows, and floor projection."""
import hashlib
import json
import re
import sys
from collections import Counter
from pathlib import Path

from sage.all import EllipticCurve_from_j, PolynomialRing, QQ, classical_modular_polynomial, matrix

HERE = Path(__file__).resolve().parent
SOURCE = HERE/'data'/'exp11_class_walk_D2631_f6.json'
sys.path.insert(0, str(HERE/'tools'))
import hecke11 as H  # noqa: E402


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rank(rows, columns, modulus=None):
    selected = [[int(row.get(str(j), 0)) for j in range(columns)] for row in rows]
    if modulus is None:
        return int(matrix(QQ, selected).rank())
    pivots = {}
    for row in selected:
        current = {j: value % modulus for j, value in enumerate(row) if value % modulus}
        while current:
            first = min(current)
            if first not in pivots:
                inv = pow(current[first], -1, modulus)
                pivots[first] = {j: value*inv % modulus for j, value in current.items()}
                break
            scale = current[first]
            for j, value in pivots[first].items():
                updated = (current.get(j, 0)-scale*value) % modulus
                if updated:
                    current[j] = updated
                else:
                    current.pop(j, None)
    return len(pivots)


def main():
    data = json.loads(SOURCE.read_text())
    assert (data['DK'],data['f'],data['p'],data['u'],data['hecke_primes']) == (-2631,6,23743,16,[2,3])
    assert len(data['column_points']) == len(set(data['column_points'])) == data['class_size']
    funcs,jfun = H.build([2,3])
    reduced = H.Reduced(23743,funcs,jfun,[2,3])
    points = []
    for encoded in data['column_points']:
        match = re.fullmatch(r'\((\d+) : (\d+) : 1\)', encoded)
        assert match, encoded
        points.append(reduced.E([int(match.group(1)),int(match.group(2)),1]))
    index = {point:i for i,point in enumerate(points)}
    phi = {ell:classical_modular_polynomial(ell) for ell in (2,3)}
    ring = PolynomialRing(reduced.Fp,'J')
    J = ring.gen()
    conductor_by_j = {}
    point_records, row_records = [], []
    strata, root_counts = Counter(), {2:Counter(),3:Counter()}
    missing_complete = []
    row_index = 0
    for i,point in enumerate(points):
        j = reduced.j(point)
        assert j is not None, i
        key = int(j)
        if key not in conductor_by_j:
            conductor_by_j[key] = int(EllipticCurve_from_j(j).endomorphism_order().conductor())
        conductor = conductor_by_j[key]
        assert 6 % conductor == 0
        strata[conductor] += 1
        point_records.append({'column':i,'j':key,'endomorphism_conductor':conductor})
        for ell in (2,3):
            predicted = ell+1 if (6//conductor)%ell == 0 else 1
            hecke_roots = reduced.neighbour_x(ell,point).roots()
            modular_roots = ring(phi[ell](j,J)).roots()
            h_count = sum(int(m) for _,m in hecke_roots)
            m_count = sum(int(m) for _,m in modular_roots)
            assert h_count == m_count == predicted, (i,ell,h_count,m_count,predicted)
            root_counts[ell][h_count] += 1
            if predicted != ell+1:
                continue
            neighbours = reduced.neighbours_all(ell,point)
            if neighbours is None:
                missing_complete.append({'column':i,'degree':ell,'reason':'neighbours_all_none'})
                continue
            assert len(neighbours) == ell+1 and all(q in index for q in neighbours)
            assert sum(neighbours,reduced.E(0)) == reduced.a_l[ell]*point
            row = Counter(index[q] for q in neighbours)
            row[i] -= reduced.a_l[ell]
            decoded = {str(k):int(v) for k,v in row.items() if v}
            assert decoded == {k:int(v) for k,v in data['relation_rows'][row_index].items() if v}, (i,ell,row_index)
            row_records.append({'row':row_index,'source_column':i,'source_conductor':conductor,'degree':ell})
            row_index += 1
    assert row_index == len(data['relation_rows']) == data['relations']
    floor = {record['column'] for record in point_records if record['endomorphism_conductor']==6}
    nonfloor = set(range(len(points)))-floor
    ranks = {}
    for label, modulus in [('QQ',None),('23',23),('1000000007',1000000007)]:
        ranks[label] = {}
        for degrees in ((2,),(3,),(2,3)):
            chosen = [row for row,meta in zip(data['relation_rows'],row_records) if meta['degree'] in degrees]
            projected = [{k:v for k,v in row.items() if int(k) in nonfloor} for row in chosen]
            ranks[label]['+'.join(map(str,degrees))] = [rank(chosen,len(points),modulus),
                                                          rank(projected,len(points),modulus)]
    expected = {'2':[384,378], '3':[192,144], '2+3':[480,426]}
    # Subset projections are measured independently; the frozen forecast fixes only the combined value.
    prediction_match = (len(points)==768 and dict(strata)=={1:96,2:96,3:288,6:288}
                        and root_counts[2]=={1:384,3:384} and root_counts[3]=={1:576,4:192}
                        and not missing_complete and all(v['2+3']==[480,426] for v in ranks.values()))
    output = {'status':'VERIFIED_FORECAST_MATCH' if prediction_match else 'VERIFIED_FORECAST_MISMATCH',
              'prediction_match':prediction_match,'source_sha256':digest(SOURCE),
              'protocol_sha256':digest(HERE/'PRODUCER_PROTOCOL.md'),
              'point_count':len(points),'distinct_j':len(conductor_by_j),
              'conductor_counts':dict(sorted(strata.items())),
              'root_counts':{str(ell):dict(sorted(root_counts[ell].items())) for ell in (2,3)},
              'missing_complete':missing_complete,'rows_checked':row_index,'ranks':ranks,
              'point_records':point_records,'row_records':row_records}
    (HERE/'audit.json').write_text(json.dumps(output,indent=2,sort_keys=True)+'\n')
    print(json.dumps({k:v for k,v in output.items() if k not in ('point_records','row_records')},sort_keys=True))


if __name__=='__main__':
    main()
