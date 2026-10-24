"""Independent integer-curve and exact-rank audit of the second frontier."""
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import runpy
import subprocess

HERE=Path(__file__).resolve().parent
FIRST=HERE.parent/'hecke-torsion-bridge-20261023'/'result.json'
FIRST_VALIDATOR=HERE.parent/'hecke-torsion-bridge-20261023'/'validate.py'
MATRIX=HERE.parent/'hecke-inert2-non3-cycle-20261023'/'full_matrix.json'
MODULE=HERE.parent/'hecke-two-sheet-small-order-20261023'/'tools'/'hecke11.py'
ops=runpy.run_path(str(FIRST_VALIDATOR))
add,mul,on_curve,sparse_rank=tuple(ops[n] for n in ('add','mul','on_curve','sparse_rank'))

def sha(path):return sha256(path.read_bytes()).hexdigest()
def key(Q):return (-1,-1) if Q is None else Q
def point(x):return None if tuple(x)==(-1,-1) else tuple(x)

def main():
    protocol=json.loads((HERE/'protocol.json').read_text())
    first=json.loads(FIRST.read_text());data=json.loads((HERE/'result.json').read_text())
    projection=json.loads((HERE/'projection_certificate.json').read_text())
    trace=json.loads((HERE/'trace_validation.json').read_text())
    original=json.loads(MATRIX.read_text())
    assert protocol['status']=='FROZEN_BEFORE_TORSION_LAYER2_PRODUCER'
    assert data['status']=='TORSION_BRIDGE_LAYER2_PRODUCED'
    assert data['protocol_sha256']==sha(HERE/'protocol.json')
    for name,path in [('first',FIRST),('matrix',MATRIX),('hecke11',MODULE),('producer',HERE/'produce.py')]:
        assert protocol['source_sha256'][name]==sha(path)
    assert data['first_sha256']==sha(FIRST) and data['source_matrix_sha256']==sha(MATRIX)
    assert data['script_sha256']==sha(HERE/'produce.py')
    assert projection['status']=='SECOND_LAYER_NEW_PROJECTION_FULL_ROW_RANK_CERTIFIED'
    assert projection['result_sha256']==sha(HERE/'result.json')
    assert projection['script_sha256']==sha(HERE/'certify_projection.py')
    assert trace['status']=='PASS_TORSION_LAYER2_TRACE_AND_MODULAR_REPLAY'
    assert trace['result_sha256']==sha(HERE/'result.json')
    assert trace['script_sha256']==sha(HERE/'validate_trace.py')
    assert trace['accepted_rows_checked']==trace['accepted_different_abs_trace_rows']==166
    pinned=subprocess.check_output(['git','show',protocol['source_commit']+':'+
                                    str(FIRST.relative_to(HERE.parent.parent))])
    assert pinned==FIRST.read_bytes()
    T=(5,5);assert on_curve(T) and mul(5,T) is None
    def orbit(Q):return min(key(add(Q,mul(k,T))) for k in range(5))
    first_keys=[tuple(x) for x in first['column_representatives']]
    old_keys={first_keys[i] for i in first['old_column_indices']}
    frontier_keys=[first_keys[i] for i in first['new_column_indices']]
    assert len(frontier_keys)==data['frontier_orbit_count']==128
    sources={}
    for col,representative in zip(first['new_column_indices'],frontier_keys):
        Q=point(representative);assert on_curve(Q) and orbit(Q)==representative
        for k in range(5):
            translated=add(Q,mul(k,T))
            assert translated not in sources
            sources[translated]=[col,k]
    assert len(sources)==data['candidate_source_count']==640
    saved={point(r['point']):r for r in data['source_records']}
    assert set(saved)==set(sources)
    assert all(saved[Q]['frontier_origin']==origin for Q,origin in sources.items())
    all_keys=[tuple(x) for x in data['column_representatives']]
    assert all_keys==sorted(set(all_keys))
    index={a:i for i,a in enumerate(all_keys)}
    old_cols=data['old_column_indices'];prior_cols=data['prior_column_indices']
    new_old=data['new_from_old_indices'];new_prior=data['new_from_prior_indices']
    assert {all_keys[i] for i in old_cols}==old_keys
    assert {all_keys[i] for i in prior_cols}==set(first_keys)
    assert sorted(old_cols+new_old)==sorted(prior_cols+new_prior)==list(range(len(all_keys)))
    assert len(new_prior)==412
    def remap(row):return {str(index[first_keys[int(j)]]):int(v) for j,v in row.items()}
    base_rows=[remap(row) for row in first['base_rows']]
    layer1_rows=[remap(row['coefficients']) for row in first['accepted_rows']]
    assert base_rows==data['base_rows'] and layer1_rows==data['layer1_rows']
    accepted=data['accepted_rows'];assert len(accepted)==166
    pivots=projection['pivot_column_indices']
    assert len(pivots)==len(set(pivots))==166 and set(pivots)<=set(new_prior)
    selected=[{j:v for j,v in row['coefficients'].items() if int(j) in set(pivots)}
              for row in accepted]
    assert sparse_rank(selected)==projection['exact_selected_minor_rank']==166
    status=Counter()
    for rec in accepted:
        Q=point(rec['source']);assert Q in sources
        assert rec['frontier_origin']==sources[Q]
        l=rec['degree'];assert l in (2,3)
        neighbours=[point(x) for x in rec['neighbours']]
        assert len(neighbours)==l+1 and all(on_curve(N) for N in neighbours)
        total=None
        for N in neighbours:total=add(total,N)
        assert total==mul(original['hecke_eigenvalues'][str(l)],Q)
        coeff=Counter(index[orbit(N)] for N in neighbours)
        coeff[index[orbit(Q)]]-=original['hecke_eigenvalues'][str(l)]
        assert {str(i):v for i,v in coeff.items() if v}==rec['coefficients']
        status[f'L{l}_ACCEPTED']+=1
    assert status['L2_ACCEPTED']==112 and status['L3_ACCEPTED']==54
    assert all(data['status_counts'][k]==v for k,v in status.items())
    prior_rows=base_rows+layer1_rows
    full_rows=prior_rows+[row['coefficients'] for row in accepted]
    set_new_old=set(new_old);set_new_prior=set(new_prior)
    projection_old=[{j:v for j,v in row.items() if int(j) in set_new_old} for row in full_rows]
    projection_prior=[{j:v for j,v in row.items() if int(j) in set_new_prior} for row in full_rows]
    def ranks(modulus=None):
        rbase=sparse_rank(base_rows,modulus)
        rprior=sparse_rank(prior_rows,modulus)
        rfull=sparse_rank(full_rows,modulus)
        rnewold=sparse_rank(projection_old,modulus)
        rnewprior=sparse_rank(projection_prior,modulus)
        return {'base_old_rank':rbase,'prior_full_rank':rprior,'full_rank':rfull,
                'new_from_old_projection_rank':rnewold,
                'induced_old_rank':rfull-rnewold,'induced_old_increment':rfull-rnewold-rbase,
                'new_from_prior_projection_rank':rnewprior,
                'induced_prior_rank':rfull-rnewprior,
                'induced_prior_increment':rfull-rnewprior-rprior}
    exact=ranks()
    expected={'base_old_rank':60,'prior_full_rank':100,'full_rank':266,
              'new_from_old_projection_rank':206,'induced_old_rank':60,
              'induced_old_increment':0,'new_from_prior_projection_rank':166,
              'induced_prior_rank':100,'induced_prior_increment':0}
    assert exact==expected
    modular={}
    for modulus in (101,1000000007):
        observed=ranks(modulus);assert observed==expected
        assert all(data['rank_results'][str(modulus)][k]==v for k,v in expected.items())
        modular[str(modulus)]=observed
    out={'status':'PASS_TORSION_LAYER2_ZERO_INDUCED_RANK_CERTIFIED',
         'protocol_sha256':sha(HERE/'protocol.json'),'result_sha256':sha(HERE/'result.json'),
         'first_validator_sha256':sha(FIRST_VALIDATOR),'validator_sha256':sha(HERE/'validate.py'),
         'projection_certificate_sha256':sha(HERE/'projection_certificate.json'),
         'trace_validation_sha256':sha(HERE/'trace_validation.json'),
         'exact_rational_ranks':exact,'independent_modular_ranks':modular,
         'candidate_source_count':len(sources),'accepted_rows':len(accepted),
         'candidate_id':None,'timing_claim':None}
    (HERE/'validation.json').write_text(json.dumps(out,sort_keys=True,indent=2)+'\n')
    print(json.dumps({'status':out['status'],'exact_rational_ranks':exact},sort_keys=True))

if __name__=='__main__':main()
