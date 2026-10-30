"""Pointwise Atkin–Lehner and Hecke multiset transport on a frozen class."""
import hashlib
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

from sage.all import QQ, classical_modular_polynomial, matrix

HERE = Path(__file__).resolve().parent
BASE = HERE.parent/'hecke-new-quotient-holdout-20261026'
SOURCE = BASE/'data'/'exp11_class_walk_D2631_f6.json'
AUDIT = BASE/'audit.json'
FLOOR = BASE/'floor_audit.json'
KERNEL = BASE/'tools'/'hecke11.py'
EXPECTED = {
    SOURCE:'3ea1440f009ad62e135f6211d56d366fda476f84e82e8bb714f4a7962629c193',
    KERNEL:'d13a8663c1beb145c0b66147305831bb15678208d126df5b69ddf5e17962b32b',
    AUDIT:'befde559f0ef0c929bdea9d07c8285d38465d6416e88cd7c7a7196ed62317036',
    FLOOR:'d0e553d08ab1cf2bc76aea5bf3ef7ca097b865e8dd8551259a29250de15ec556',
}
sys.path.insert(0,str(BASE/'tools'))
import hecke11 as H  # noqa: E402


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def vector_key(row):
    return tuple(sorted((int(k),int(v)) for k,v in row.items() if v))


def main():
    for path,expected in EXPECTED.items():
        assert digest(path)==expected,path
    data,audit,floor = [json.loads(path.read_text()) for path in (SOURCE,AUDIT,FLOOR)]
    funcs,jfun = H.build([2,3])
    reduced = H.Reduced(23743,funcs,jfun,[2,3])
    points=[]
    for encoded in data['column_points']:
        match=re.fullmatch(r'\((\d+) : (\d+) : 1\)',encoded)
        assert match,encoded
        points.append(reduced.E([int(match.group(1)),int(match.group(2)),1]))
    index={point:i for i,point in enumerate(points)}
    T=reduced.E([16,23682,1])
    assert 5*T==reduced.E(0)
    mapped=[T-point for point in points]
    missing_class=[i for i,point in enumerate(mapped) if point not in index]
    if missing_class:
        result={'status':'FAIL_CLASS_PERMUTATION','missing_class':missing_class}
        (HERE/'scan.json').write_text(json.dumps(result,indent=2)+'\n')
        print(json.dumps(result))
        return
    permutation=[index[point] for point in mapped]
    involution=all(permutation[permutation[i]]==i for i in range(len(points)))
    conductor=[item['endomorphism_conductor'] for item in audit['point_records']]
    conductor_preserved=all(conductor[i]==conductor[permutation[i]] for i in range(len(points)))
    phi11=classical_modular_polynomial(11)
    j_values=[reduced.j(point) for point in points]
    modular_mismatch=[]
    for i,j in enumerate(j_values):
        if j is None or j_values[permutation[i]] is None or phi11(j,j_values[permutation[i]])!=0:
            modular_mismatch.append(i)
    rows=[{int(k):int(v) for k,v in row.items() if v} for row in data['relation_rows']]
    row_by_source={(item['source_column'],item['degree']):item['row'] for item in audit['row_records']}
    row_map={}
    missing_complete=[]
    neighbour_mismatch=[]
    row_mismatch=[]
    for item in audit['row_records']:
        source,ell,r = item['source_column'],item['degree'],item['row']
        wsource=permutation[source]
        target=row_by_source.get((wsource,ell))
        if target is None:
            missing_complete.append({'row':r,'degree':ell,'source':source,'mapped_source':wsource})
            continue
        row_map[r]=target
        before=reduced.neighbours_all(ell,points[source])
        after=reduced.neighbours_all(ell,points[wsource])
        if before is None or after is None:
            missing_complete.append({'row':r,'degree':ell,'reason':'neighbour_reconstruction_none'})
            continue
        expected=Counter(permutation[index[point]] for point in before)
        actual=Counter(index[point] for point in after)
        if expected!=actual:
            neighbour_mismatch.append({'row':r,'degree':ell,'expected':dict(expected),'actual':dict(actual)})
        transformed=Counter()
        for col,value in rows[r].items():
            transformed[permutation[col]]+=value
        transformed={col:value for col,value in transformed.items() if value}
        if transformed!=rows[target]:
            row_mismatch.append({'row':r,'mapped_row':target,'expected':transformed,'actual':rows[target]})
    atkin_mismatch=[]
    for i,row in enumerate(data['atkin_lehner_rows']):
        expected=Counter({i:1})
        expected[permutation[i]]+=1
        expected={col:value for col,value in expected.items() if value}
        actual={int(k):int(v) for k,v in row.items() if v}
        if actual!=expected:
            atkin_mismatch.append(i)
    cycle_vectors=[{int(k):int(v) for k,v in certificate['signed_floor_columns'].items()}
                   for certificate in floor['cycles']]
    pair_vectors=[{int(k):int(v) for k,v in certificate['signed_floor_columns'].items()}
                  for certificate in floor['pairs']]
    def action(vectors):
        lookup={vector_key(vector):(i,1) for i,vector in enumerate(vectors)}
        lookup.update({vector_key({col:-value for col,value in vector.items()}):(i,-1)
                       for i,vector in enumerate(vectors)})
        output=[]
        for vector in vectors:
            transported={permutation[col]:value for col,value in vector.items()}
            match=lookup.get(vector_key(transported))
            output.append(None if match is None else {'target':match[0],'sign':match[1]})
        return output
    cycle_action=action(cycle_vectors)
    pair_action=action(pair_vectors)
    cycle_rowsets=[set(int(i) for i in c['signed_rows']) for c in floor['cycles']]
    cycle_row_action=[]
    for source_rows in cycle_rowsets:
        transformed={row_map[i] for i in source_rows if i in row_map}
        targets=[i for i,rowset in enumerate(cycle_rowsets) if transformed==rowset]
        cycle_row_action.append(targets[0] if len(targets)==1 else None)
    all_vectors=cycle_vectors+pair_vectors
    transported_vectors=[{permutation[col]:value for col,value in vector.items()} for vector in all_vectors]
    columns=len(points)
    span_rank=int(matrix(QQ,[[vector.get(col,0) for col in range(columns)]
                             for vector in all_vectors+transported_vectors]).rank())
    counts=Counter(item['degree'] for item in audit['row_records'])
    pass_all=(len(points)==768 and involution and conductor_preserved and not modular_mismatch
              and len(row_map)==576 and not missing_complete and not neighbour_mismatch
              and not row_mismatch and not atkin_mismatch and span_rank==54)
    result={'status':'VERIFIED_POINTWISE_COMMUTATION' if pass_all else 'POINTWISE_MISMATCH',
            'point_count':len(points),'complete_row_counts':dict(counts),'torsion_order':5,
            'class_permutation':permutation,'involution':involution,
            'conductor_preserved':conductor_preserved,'modular_mismatch':modular_mismatch,
            'missing_complete':missing_complete,'neighbour_mismatch':neighbour_mismatch,
            'row_mismatch':row_mismatch,'atkin_mismatch':atkin_mismatch,
            'row_map':{str(k):v for k,v in row_map.items()},
            'cycle_vector_action':cycle_action,'pair_vector_action':pair_action,
            'cycle_row_action':cycle_row_action,'transported_witness_span_rank_QQ':span_rank,
            'source_hashes':{str(path.relative_to(HERE.parent)):digest(path) for path in EXPECTED}}
    (HERE/'scan.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('class_permutation','row_map')},sort_keys=True))


if __name__=='__main__':main()
