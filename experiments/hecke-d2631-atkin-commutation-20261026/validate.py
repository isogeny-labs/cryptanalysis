"""Independent permutation replay against the frozen integer matrices."""
import hashlib
import json
from collections import Counter
from pathlib import Path

HERE=Path(__file__).resolve().parent
BASE=HERE.parent/'hecke-new-quotient-holdout-20261026'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def key(row):
    return tuple(sorted((int(k),int(v)) for k,v in row.items() if v))


def main():
    scan_path=HERE/'scan.json'
    source_path=BASE/'data'/'exp11_class_walk_D2631_f6.json'
    audit_path=BASE/'audit.json'
    floor_path=BASE/'floor_audit.json'
    scan,source,audit,floor=[json.loads(path.read_text()) for path in
                             (scan_path,source_path,audit_path,floor_path)]
    assert scan['status']=='VERIFIED_POINTWISE_COMMUTATION'
    permutation=scan['class_permutation']
    assert len(permutation)==768 and sorted(permutation)==list(range(768))
    assert all(permutation[permutation[i]]==i for i in range(768))
    conductor=[item['endomorphism_conductor'] for item in audit['point_records']]
    assert all(conductor[i]==conductor[permutation[i]] for i in range(768))
    rows=[{int(k):int(v) for k,v in row.items() if v} for row in source['relation_rows']]
    row_by_source={(item['source_column'],item['degree']):item['row'] for item in audit['row_records']}
    row_map={int(k):v for k,v in scan['row_map'].items()}
    assert len(row_map)==576 and sorted(row_map)==list(range(576))
    assert sorted(row_map.values())==list(range(576))
    for item in audit['row_records']:
        i,degree,r=item['source_column'],item['degree'],item['row']
        assert row_map[r]==row_by_source[(permutation[i],degree)]
        transformed=Counter()
        for col,value in rows[r].items():
            transformed[permutation[col]]+=value
        assert key(transformed)==key(rows[row_map[r]])
    for i,row in enumerate(source['atkin_lehner_rows']):
        expected=Counter({i:1})
        expected[permutation[i]]+=1
        assert key(expected)==key(row)
    def replay_action(name,certificate_key,vector_key):
        certificates=floor[certificate_key]
        action=scan[name]
        assert len(certificates)==len(action)
        targets=[]
        for i,certificate in enumerate(certificates):
            result=action[i]
            assert result is not None
            target=result['target']
            sign=result['sign']
            assert sign in (-1,1)
            original={int(k):int(v) for k,v in certificate[vector_key].items()}
            transported={permutation[col]:value for col,value in original.items()}
            expected={int(k):sign*int(v) for k,v in certificates[target][vector_key].items()}
            assert transported==expected
            targets.append(target)
        assert sorted(targets)==list(range(len(certificates)))
        assert all(action[action[i]['target']]['target']==i and
                   action[action[i]['target']]['sign']*action[i]['sign']==1
                   for i in range(len(action)))
        return targets
    cycle_targets=replay_action('cycle_vector_action','cycles','signed_floor_columns')
    pair_targets=replay_action('pair_vector_action','pairs','signed_floor_columns')
    assert cycle_targets==scan['cycle_row_action']
    assert all(i!=target for i,target in enumerate(cycle_targets))
    assert all(i!=target for i,target in enumerate(pair_targets))
    cycle_orbits=[[i,target] for i,target in enumerate(cycle_targets) if i<target]
    pair_orbits=[[i,target] for i,target in enumerate(pair_targets) if i<target]
    assert len(cycle_orbits)==3 and len(pair_orbits)==24
    result={'status':'VERIFIED_INTEGER_PERMUTATION_REPLAY',
            'scan_sha256':digest(scan_path),'source_sha256':digest(source_path),
            'row_count':len(rows),'cycle_action':cycle_targets,
            'cycle_orbits':cycle_orbits,'pair_orbits':pair_orbits,
            'pair_count':len(pair_targets),'atkin_rows_checked':len(source['atkin_lehner_rows'])}
    (HERE/'validation.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps(result,sort_keys=True))


if __name__=='__main__':main()
