"""Independent exact-arithmetic audit of the second inert-2 matrix."""
from collections import Counter
from fractions import Fraction
from hashlib import sha256
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
SOURCE=HERE.parent/'hecke-two-sheet-small-order-20261023'

def sha(path): return sha256(path.read_bytes()).hexdigest()
def read(name): return json.loads((HERE/name).read_text())

def rank(rows,columns,modulus=None):
    if modulus is None:
        a=[[Fraction(row.get(str(j),0)) for j in columns] for row in rows]
    else:
        a=[[int(row.get(str(j),0))%modulus for j in columns] for row in rows]
    pivot_row=0
    for col in range(len(columns)):
        pivot=next((i for i in range(pivot_row,len(a)) if a[i][col]),None)
        if pivot is None: continue
        a[pivot_row],a[pivot]=a[pivot],a[pivot_row]
        scale=a[pivot_row][col]
        inverse=(1/scale if modulus is None else pow(scale,-1,modulus))
        a[pivot_row]=[(v*inverse if modulus is None else v*inverse%modulus)
                      for v in a[pivot_row]]
        for i in range(pivot_row+1,len(a)):
            factor=a[i][col]
            if factor:
                a[i]=[(v-factor*w if modulus is None else (v-factor*w)%modulus)
                      for v,w in zip(a[i],a[pivot_row])]
        pivot_row+=1
        if pivot_row==len(a): break
    return pivot_row

def dense_combination(rows,terms,width):
    result=[Fraction(0)]*width
    for row_id,coeff in terms.items():
        for col,value in rows[int(row_id)].items():
            result[int(col)]+=Fraction(coeff)*value
    return result

def main():
    selection=read('selection.json');gate_protocol=read('gate_protocol.json')
    gate=read('fiber_gate.json');protocol=read('producer_protocol_v2.json')
    data=read('full_matrix.json');cert=read('certificates.json');failure=read('producer_failure.json')
    chosen=selection['chosen']
    assert selection['status']=='SECOND_INERT2_HOLDOUT_SELECTED'
    assert (chosen['d'],chosen['p'],chosen['v'],chosen['h1'],chosen['h2'],chosen['h3'],chosen['h6'])==(131,13723,112,5,15,10,30)
    assert selection['selection_protocol_sha256']==sha(HERE/'selection_protocol.json')
    assert selection['script_sha256']==sha(HERE/'select.py')
    assert gate_protocol['selection_sha256']==sha(HERE/'selection.json')
    assert gate_protocol['source_sha256']=={'gate':sha(SOURCE/'fiber_gate.py'),
                                            'hecke11':sha(SOURCE/'tools/hecke11.py')}
    assert gate['status']=='PASS_UNIFORM_TWO_SHEET_GATE' and not gate['exceptions']
    assert gate['script_sha256']==sha(SOURCE/'fiber_gate.py')
    assert {c:x['rational_point_count'] for c,x in gate['strata'].items()}==gate_protocol['predicted_points_by_conductor']
    assert failure['status']=='PRE_RANK_PRODUCER_FAILURE' and not failure['matrix_emitted']
    assert failure['script_sha256']==sha(HERE/'produce.py')
    assert failure['protocol_sha256']==sha(HERE/'producer_protocol.json')
    assert protocol['status']=='FROZEN_BEFORE_SECOND_INERT2_MATRIX_PRIME_FIX'
    for k,path in [('source',HERE/'produce_v2.py'),('hecke11',SOURCE/'tools/hecke11.py'),
                   ('selection',HERE/'selection.json'),('gate',HERE/'fiber_gate.json')]:
        assert protocol['source_sha256'][k]==sha(path)
    assert data['status']=='SECOND_INERT2_FULL_MATRIX_PRODUCED'
    assert data['producer_protocol_sha256']==sha(HERE/'producer_protocol_v2.json')
    assert data['script_sha256']==sha(HERE/'produce_v2.py')
    assert data['hecke11_sha256']==sha(SOURCE/'tools/hecke11.py')
    assert cert['full_matrix_sha256']==sha(HERE/'full_matrix.json')
    assert cert['script_sha256']==sha(HERE/'certify.py')
    points=data['column_points'];rows=data['relation_rows'];meta=data['row_records']
    assert (len(points),len(rows),len(meta))==(120,70,70)
    assert [p['column'] for p in points]==list(range(120))
    assert len({tuple(p['point']) for p in points})==120
    assert dict(Counter(str(p['conductor']) for p in points))==protocol['predicted_points_by_conductor']
    assert Counter((m['conductor'],m['degree']) for m in meta)=={(1,2):10,(1,3):10,(2,3):30,(3,2):20}
    assert [m['row'] for m in meta]==list(range(70))
    assert data['hecke_eigenvalues']=={'2':-2,'3':-1}
    assert data['rational_root_counts']=={'2':{'1':90,'3':30},'3':{'1':80,'4':40}}
    c2_rows=[m['row'] for m in meta if (m['conductor'],m['degree'])==(2,3)]
    others=[i for i in range(70) if i not in c2_rows]
    nonfloor=[p['column'] for p in points if p['conductor']!=6]
    floor=[p['column'] for p in points if p['conductor']==6]
    assert (len(c2_rows),len(others),len(nonfloor),len(floor))==(30,40,60,60)
    c2_cols={p['column'] for p in points if p['conductor']==2}
    assert set(int(x) for v in data['c1_degree2_to_c2'].values() for x in v)==c2_cols
    assert all(len(v)==3 and len(set(v))==3 for v in data['c1_degree2_to_c2'].values())
    row_for={(m['source'],m['degree']):m['row'] for m in meta}
    adjacency={}
    for source in c2_cols:
        counts=Counter({int(j):v for j,v in rows[row_for[(source,3)]].items()})
        counts[source]+=data['hecke_eigenvalues']['3']
        assert all(v>=0 for v in counts.values())
        neighbours=[j for j,n in counts.items() for _ in range(n)]
        assert len(neighbours)==4
        horizontal={j for j in neighbours if j in c2_cols}
        assert len(horizontal)==2
        assert len([j for j in neighbours if points[j]['conductor']==6])==2
        adjacency[source]=horizontal
    assert all(source in adjacency[other] for source,ns in adjacency.items() for other in ns)
    unseen=set(c2_cols);cycle_lengths=[]
    while unseen:
        component=set();stack=[min(unseen)]
        while stack:
            vertex=stack.pop()
            if vertex in component: continue
            component.add(vertex);stack.extend(adjacency[vertex]-component)
        unseen-=component;cycle_lengths.append(len(component))
    assert sorted(cycle_lengths)==[15,15]
    local=cert['local_commutator_relations'];assert len(local)==10
    supports=[]
    for rec in local:
        assert len(rec['c2_rows'])==len(set(rec['c2_rows']))==3
        assert set(rec['c2_rows'])<=set(c2_rows)
        assert set(map(int,rec['other_terms']))<=set(others)
        assert dense_combination(rows,{str(i):1 for i in rec['c2_rows']},120)==dense_combination(rows,rec['other_terms'],120)
        supports.extend(rec['c2_rows'])
    assert len(set(supports))==30 and set(supports)==set(c2_rows)
    basis=cert['projected_left_kernel_basis'];assert len(basis)==14
    basis_dense=[{str(i):Fraction(v.get(str(i),0)) for i in range(70)} for v in basis]
    assert rank(basis_dense,list(range(70)))==14
    images=[]
    for terms in basis:
        image=dense_combination(rows,terms,120)
        assert all(image[j]==0 for j in nonfloor)
        images.append(image)
    chosen_floor=[]
    for rec in cert['floor_only_vectors']:
        i=rec['kernel_index'];assert 0<=i<14
        vector=images[i]
        assert vector==[Fraction(rec['coordinates'].get(str(j),0)) for j in range(120)]
        chosen_floor.append({str(j):vector[j] for j in floor})
    assert len(chosen_floor)==4 and rank(chosen_floor,floor)==4
    expected={'full_QQ':60,'nonfloor_QQ':56,'others_full_QQ':40,'others_nonfloor_QQ':40,
              'c2_full_QQ':30,'c2_nonfloor_QQ':26,'c2_increment_full_QQ':20,
              'c2_increment_nonfloor_QQ':16,'floor_only_row_directions':4}
    assert data['ranks']==expected
    row_sets={'full':rows,'others_full':[rows[i] for i in others],
              'c2_full':[rows[i] for i in c2_rows]}
    ranks={}
    for name,source_rows in row_sets.items():
        ranks[name]=rank(source_rows,list(range(120)))
        ranks[name.replace('_full','')+'_nonfloor' if name!='full' else 'nonfloor']=rank(source_rows,nonfloor)
    assert ranks=={'full':60,'nonfloor':56,'others_full':40,'others_nonfloor':40,
                   'c2_full':30,'c2_nonfloor':26}
    modular={}
    for q in (101,1000000007,2147483647):
        modular[str(q)]={name:rank(source_rows,cols,q)
                         for name,source_rows in row_sets.items()
                         for cols in (list(range(120)),nonfloor)
                         for name in ([name] if len(cols)==120 else
                                      [name.replace('_full','')+'_nonfloor' if name!='full' else 'nonfloor'])}
        assert modular[str(q)]==ranks
    out={'status':'PASS_SECOND_INERT2_POSITIVE_INCREMENT_CERTIFIED',
         'selection_protocol_sha256':sha(HERE/'selection_protocol.json'),
         'gate_protocol_sha256':sha(HERE/'gate_protocol.json'),
         'producer_protocol_v2_sha256':sha(HERE/'producer_protocol_v2.json'),
         'full_matrix_sha256':sha(HERE/'full_matrix.json'),
         'certificates_sha256':sha(HERE/'certificates.json'),
         'producer_failure_sha256':sha(HERE/'producer_failure.json'),
         'validator_sha256':sha(HERE/'validate.py'),
         'exact_local_relations':10,'independent_projected_kernel_vectors':14,
         'independent_floor_only_vectors':4,'exact_ranks':ranks,
         'c2_degree3_horizontal_cycle_lengths':sorted(cycle_lengths),
         'independent_modular_ranks':modular,
         'candidate_id':None,'timing_claim':None}
    (HERE/'validation.json').write_text(json.dumps(out,sort_keys=True,indent=2)+'\n')
    print(json.dumps({'status':out['status'],'exact_ranks':ranks},sort_keys=True))

if __name__=='__main__':main()
