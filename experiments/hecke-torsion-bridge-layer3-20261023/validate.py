"""Independent integer-point and exact-rank audit of the third frontier."""
from collections import Counter
from fractions import Fraction
from hashlib import sha256
import json
from pathlib import Path
import runpy
import subprocess
import time

HERE=Path(__file__).resolve().parent
PREV=HERE.parent/'hecke-torsion-bridge-layer2-20261023'/'result.json'
PREV_VALIDATOR=HERE.parent/'hecke-torsion-bridge-layer2-20261023'/'validate.py'
FIRST=HERE.parent/'hecke-torsion-bridge-20261023'/'result.json'
MODULE=HERE.parent/'hecke-two-sheet-small-order-20261023'/'tools'/'hecke11.py'
ops=runpy.run_path(str(PREV_VALIDATOR))
add,mul,on_curve,sparse_rank=tuple(ops[n] for n in ('add','mul','on_curve','sparse_rank'))

def sha(path):return sha256(path.read_bytes()).hexdigest()
def key(Q):return (-1,-1) if Q is None else Q
def point(x):return None if tuple(x)==(-1,-1) else tuple(x)

def main():
    protocol=json.loads((HERE/'protocol.json').read_text())
    previous=json.loads(PREV.read_text());first=json.loads(FIRST.read_text())
    data=json.loads((HERE/'result.json').read_text())
    certificate=json.loads((HERE/'closed_certificates.json').read_text())
    trace=json.loads((HERE/'trace_validation.json').read_text())
    formal=json.loads((HERE/'formal/build.json').read_text())
    assert protocol['status']=='FROZEN_BEFORE_TORSION_LAYER3_PRODUCER'
    assert data['status']=='TORSION_BRIDGE_LAYER3_PRODUCED'
    assert data['protocol_sha256']==sha(HERE/'protocol.json')
    for name,path in [('previous',PREV),('first',FIRST),('hecke11',MODULE),('producer',HERE/'produce.py')]:
        assert protocol['source_sha256'][name]==sha(path)
    assert data['previous_sha256']==sha(PREV) and data['first_sha256']==sha(FIRST)
    assert data['script_sha256']==sha(HERE/'produce.py')
    assert certificate['status']=='EXACT_THIRD_FRONTIER_CLOSED_COMBINATIONS_CERTIFIED'
    assert certificate['result_sha256']==sha(HERE/'result.json')
    assert certificate['certificate_protocol_sha256']==sha(HERE/'certificate_protocol.json')
    assert certificate['script_sha256']==sha(HERE/'certify_closed.py')
    assert trace['status']=='PASS_TORSION_LAYER3_TRACE_AND_MODULAR_REPLAY'
    assert trace['result_sha256']==sha(HERE/'result.json')
    assert trace['script_sha256']==sha(HERE/'validate_trace.py')
    assert trace['accepted_rows_checked']==trace['accepted_different_abs_trace_rows']==568
    assert formal['status']=='LEAN_CLOSED_BRIDGE_THEOREMS_BUILT'
    assert formal['source_sha256']==sha(HERE/'formal/ClosedBridge.lean')
    assert formal['output_sha256']==sha(HERE/'formal/build-output.txt')
    assert formal['axioms']==["'ClosedBridge.closed_image_gives_constraint' depends on axioms: [propext]",
                              "'ClosedBridge.no_new_constraint_of_closed_images_mem' depends on axioms: [propext, Quot.sound]"]
    pinned=subprocess.check_output(['git','show',protocol['source_commit']+':'+
                                    str(PREV.relative_to(HERE.parent.parent))])
    assert pinned==PREV.read_bytes()
    T=(5,5);assert on_curve(T) and mul(5,T) is None
    def orbit(Q):return min(key(add(Q,mul(k,T))) for k in range(5))
    previous_keys=[tuple(x) for x in previous['column_representatives']]
    old_keys={previous_keys[i] for i in previous['old_column_indices']}
    first_keys=[tuple(x) for x in first['column_representatives']]
    frontier_keys=[previous_keys[i] for i in previous['new_from_prior_indices']]
    assert (len(previous_keys),len(frontier_keys))==(657,412)
    sources={}
    for col,representative in zip(previous['new_from_prior_indices'],frontier_keys):
        Q=point(representative);assert on_curve(Q) and orbit(Q)==representative
        for k in range(5):
            translated=add(Q,mul(k,T))
            assert translated not in sources
            sources[translated]=[col,k]
    assert len(sources)==data['candidate_source_count']==2060
    saved={point(r['point']):r for r in data['source_records']}
    assert set(saved)==set(sources)
    assert all(saved[Q]['frontier_origin']==origin for Q,origin in sources.items())
    all_keys=[tuple(x) for x in data['column_representatives']]
    assert all_keys==sorted(set(all_keys))
    index={a:i for i,a in enumerate(all_keys)}
    boundaries={'old':(data['old_column_indices'],old_keys),
                'first':(data['first_column_indices'],set(first_keys)),
                'previous':(data['previous_column_indices'],set(previous_keys))}
    for name,(indices,keys) in boundaries.items():
        assert {all_keys[i] for i in indices}==keys
        assert sorted(indices+data['discard_'+name+'_indices'])==list(range(len(all_keys)))
    assert len(data['discard_previous_indices'])==883
    def remap(row):return {str(index[previous_keys[int(j)]]):int(v) for j,v in row.items()}
    base_rows=[remap(row) for row in previous['base_rows']]
    layer1_rows=[remap(row) for row in previous['layer1_rows']]
    layer2_rows=[remap(row['coefficients']) for row in previous['accepted_rows']]
    assert base_rows==data['base_rows'] and layer1_rows==data['layer1_rows']
    assert layer2_rows==data['layer2_rows']
    accepted=data['accepted_rows'];status=Counter()
    for rec in accepted:
        Q=point(rec['source']);assert Q in sources
        assert rec['frontier_origin']==sources[Q]
        l=rec['degree'];assert l in (2,3)
        nb=[point(x) for x in rec['neighbours']]
        assert len(nb)==l+1 and all(on_curve(N) for N in nb)
        total=None
        for N in nb:total=add(total,N)
        assert total==mul(-2 if l==2 else -1,Q)
        coeff=Counter(index[orbit(N)] for N in nb)
        coeff[index[orbit(Q)]]-=(-2 if l==2 else -1)
        assert {str(i):v for i,v in coeff.items() if v}==rec['coefficients']
        status[f'L{l}_ACCEPTED']+=1
    assert len(accepted)==568 and sum(status.values())==568
    assert all(data['status_counts'][k]==v for k,v in status.items())
    full_rows=base_rows+layer1_rows+layer2_rows+[row['coefficients'] for row in accepted]
    assert len(full_rows)==844
    projections={name:[{j:v for j,v in row.items() if int(j) in set(data['discard_'+name+'_indices'])}
                       for row in full_rows] for name in ('old','first','previous')}
    start=time.monotonic()
    exact={'base_old_rank':60,'first_full_rank':100,'previous_full_rank':266,
           'full_rank':sparse_rank(full_rows)}
    for name,baseline in (('old',60),('first',100),('previous',266)):
        projected=sparse_rank(projections[name])
        exact['discard_'+name+'_projection_rank']=projected
        exact['induced_'+name+'_rank']=exact['full_rank']-projected
        exact['induced_'+name+'_increment']=exact['induced_'+name+'_rank']-baseline
    exact_wall=time.monotonic()-start
    for name,baseline_count,baseline_rank in [('previous',276,266),('first',110,100),('old',70,60)]:
        part=certificate['boundaries'][name]
        discarded=set(data['discard_'+name+'_indices'])
        retained=set(data[name+'_column_indices'])
        assert part['discarded_projection_rank']==exact['discard_'+name+'_projection_rank']
        assert part['closed_combination_count']==844-part['discarded_projection_rank']
        assert part['nontrivial_combination_count']==len(part['records'])
        assert part['nontrivial_combination_count']==part['closed_combination_count']-baseline_count
        coefficient_rows=[];selected_images=[];selected_indices=[]
        for i,record in enumerate(part['records']):
            combo={int(j):Fraction(v) for j,v in record['combination'].items()}
            assert any(j>=baseline_count for j in combo)
            coefficient_rows.append({str(j):v for j,v in combo.items() if j>=baseline_count})
            combined={}
            for row_id,factor in combo.items():
                for col,value in full_rows[row_id].items():
                    j=int(col);new=combined.get(j,0)+factor*value
                    if new:combined[j]=new
                    else:combined.pop(j,None)
            assert not (set(combined)&discarded)
            image={str(j):v for j,v in combined.items() if j in retained}
            assert {str(j):str(v) for j,v in combined.items() if j in retained}==record['retained_image']
            is_novel=sparse_rank(full_rows[:baseline_count]+selected_images+[image])>baseline_rank+len(selected_images)
            assert is_novel==record['selected_as_novel']
            if is_novel:selected_images.append(image);selected_indices.append(i)
        assert sparse_rank(coefficient_rows)==len(coefficient_rows)
        assert selected_indices==part['selected_novel_indices']
        assert len(selected_images)==part['induced_increment']==exact['induced_'+name+'_increment']
        assert baseline_rank+len(selected_images)==part['induced_rank']==exact['induced_'+name+'_rank']
    modular={}
    for modulus in (101,1000000007):
        measured={'base_old_rank':60,'first_full_rank':100,'previous_full_rank':266,
                  'full_rank':sparse_rank(full_rows,modulus)}
        for name,baseline in (('old',60),('first',100),('previous',266)):
            projected=sparse_rank(projections[name],modulus)
            measured['discard_'+name+'_projection_rank']=projected
            measured['induced_'+name+'_rank']=measured['full_rank']-projected
            measured['induced_'+name+'_increment']=measured['induced_'+name+'_rank']-baseline
        modular[str(modulus)]=measured
        assert all(data['rank_results'][str(modulus)][k]==v for k,v in measured.items())
        assert measured==exact
    out={'status':'PASS_TORSION_LAYER3_EXACT_INDUCED_RANK_CERTIFIED',
         'protocol_sha256':sha(HERE/'protocol.json'),'result_sha256':sha(HERE/'result.json'),
         'previous_validator_sha256':sha(PREV_VALIDATOR),'validator_sha256':sha(HERE/'validate.py'),
         'closed_certificates_sha256':sha(HERE/'closed_certificates.json'),
         'trace_validation_sha256':sha(HERE/'trace_validation.json'),
         'formal_build_sha256':sha(HERE/'formal/build.json'),
         'exact_rational_ranks':exact,'independent_modular_ranks':modular,
         'exact_rank_wall_s_diagnostic':exact_wall,
         'candidate_source_count':len(sources),'accepted_rows':len(accepted),
         'candidate_id':None,'timing_claim':None}
    (HERE/'validation.json').write_text(json.dumps(out,sort_keys=True,indent=2)+'\n')
    print(json.dumps({'status':out['status'],'exact_rational_ranks':exact},sort_keys=True))

if __name__=='__main__':main()
