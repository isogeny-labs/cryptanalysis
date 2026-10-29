"""Audit the cyclic-16 B-fiber factor in two independent source images."""
import json
from collections import Counter,defaultdict
from hashlib import sha256
from pathlib import Path

HERE=Path(__file__).resolve().parent


def main():
    path=HERE/'factor_protocol.json'
    protocol=json.loads(path.read_text())
    assert protocol['status']=='FROZEN_BEFORE_RETROSPECTIVE_16_PATH_FACTOR_AUDIT'
    for name,rec in protocol['inputs'].items():
        assert sha256(Path(rec['path']).read_bytes()).hexdigest()==rec['sha256'],name
    result={'status':'MEASURED_UNIT_16_PATH_B_FACTOR','protocol_sha256':sha256(path.read_bytes()).hexdigest(),
            'source_code_sha256':sha256(Path(__file__).read_bytes()).hexdigest(),'primes':{}}
    for p in protocol['primes']:
        census=json.loads(Path(protocol['inputs'][f'p{p}_source_census.json']['path']).read_text())
        image=json.loads(Path(protocol['inputs'][f'p{p}_source_image.json']['path']).read_text())
        audit=json.loads(Path(protocol['inputs'][f'p{p}_audit.json']['path']).read_text())
        assert census['prime']==image['prime']==audit['prime']==p
        models=[r for r in census['rows'] if r['j']==1728%p]
        assert len(models)==1
        model=models[0]
        ainvs=model['curve_ainvs']
        rows=[r for r in image['rows'] if r['source_ainvs']==ainvs]
        assert len(rows)==model['paired_chain_count']
        cells=defaultdict(set)
        signatures=Counter()
        for row in rows:
            i,j=row['pair']
            assert row['source_j']==1728%p and len(row['B_candidates'])==1
            b=row['B_candidates'][0]
            assert b is not None
            signature=tuple([1728%p,*(e['target_j'] for e in model['three_paths'][j])])
            cells[(signature,tuple(b),j)].add(i)
            signatures[signature]+=1
        factors=[{'j_sequence':list(sig),'B_point':list(b),'path_27_index':j,
                  'path_16_indices':sorted(iset),'factor':len(iset)}
                 for (sig,b,j),iset in sorted(cells.items())]
        assert factors and all(x['factor']==1 for x in factors)
        result['primes'][str(p)]={'j1728_source_ainvs':ainvs,
                                 'rational_27_paths':len(model['three_paths']),
                                 'rational_16_paths':len(model['two_paths']),
                                 'source_chains':len(rows),
                                 'distinct_B_points':len({tuple(r['B_candidates'][0]) for r in rows}),
                                 'factor_histogram':dict(Counter(x['factor'] for x in factors)),
                                 'j_sequence_chain_counts':[{'j_sequence':list(k),'chains':n} for k,n in sorted(signatures.items())],
                                 'cells':factors}
        print(json.dumps({'prime':p,'chains':len(rows),'B_points':result['primes'][str(p)]['distinct_B_points'],
                          'factor_histogram':result['primes'][str(p)]['factor_histogram']},sort_keys=True),flush=True)
    (HERE/'factor_result.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')


if __name__=='__main__':main()
