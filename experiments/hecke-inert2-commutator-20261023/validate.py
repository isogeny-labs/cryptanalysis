"""Independent standard-Python audit of the inert-2 rank and certificates."""
from collections import Counter
from fractions import Fraction
from hashlib import sha256
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
SOURCE=HERE.parent/'hecke-two-sheet-small-order-20261023'


def digest(path):return sha256(path.read_bytes()).hexdigest()


def rank_mod(rows,cols,q):
    a=[[int(row.get(str(j),0))%q for j in cols] for row in rows]
    rank=0
    for j in range(len(cols)):
        pivot=next((k for k in range(rank,len(a)) if a[k][j]),None)
        if pivot is None:continue
        a[rank],a[pivot]=a[pivot],a[rank]
        inv=pow(a[rank][j],-1,q)
        a[rank]=[(v*inv)%q for v in a[rank]]
        for k in range(rank+1,len(a)):
            if a[k][j]:
                f=a[k][j]
                a[k]=[(v-f*w)%q for v,w in zip(a[k],a[rank])]
        rank+=1
        if rank==len(a):break
    return rank


def rank_fraction(rows):
    a=[[Fraction(x) for x in row] for row in rows]
    rank=0
    for j in range(len(a[0])):
        pivot=next((k for k in range(rank,len(a)) if a[k][j]),None)
        if pivot is None:continue
        a[rank],a[pivot]=a[pivot],a[rank]
        scale=a[rank][j]
        a[rank]=[v/scale for v in a[rank]]
        for k in range(rank+1,len(a)):
            if a[k][j]:
                f=a[k][j]
                a[k]=[v-f*w for v,w in zip(a[k],a[rank])]
        rank+=1
        if rank==len(a):break
    return rank


def combine(rows,terms):
    v=[Fraction(0) for _ in range(48)]
    for row_id,coeff in terms.items():
        for col,value in rows[int(row_id)].items():
            v[int(col)]+=Fraction(coeff)*value
    return v


def main():
    selection=json.loads((HERE/'selection.json').read_text())
    gate=json.loads((HERE/'fiber_gate.json').read_text())
    protocol=json.loads((HERE/'producer_protocol_v3.json').read_text())
    data=json.loads((HERE/'full_matrix_v3.json').read_text())
    cert=json.loads((HERE/'certificates.json').read_text())
    provenance=json.loads((HERE/'provenance_correction.json').read_text())
    diag=json.loads((HERE/'conductor_diagnostic.json').read_text())
    edges=json.loads((HERE/'edge_diagnostic.json').read_text())
    bug=json.loads((HERE/'sage_bug_receipt.json').read_text())
    failures=json.loads((HERE/'producer_failures.json').read_text())
    assert selection['status']=='INERT2_HOLDOUT_SELECTED' and selection['chosen']['d']==35
    assert selection['selection_protocol_sha256']==digest(HERE/'selection_protocol.json')
    assert selection['script_sha256']==digest(HERE/'select.py')
    assert gate['status']=='PASS_UNIFORM_TWO_SHEET_GATE'
    assert protocol['status']=='FROZEN_BEFORE_CORRECTED_MULTIPLICITY_AWARE_MATRIX'
    assert failures['status']=='PRESERVED_PRE_RANK_PRODUCER_FAILURES'
    assert [r['version'] for r in failures['runs']]==['v1','v2']
    for r,source_file,protocol_file in zip(failures['runs'],('produce.py','produce_v2.py'),
                                           ('producer_protocol.json','producer_protocol_v2.json')):
        assert r['script_sha256']==digest(HERE/source_file)
        assert r['protocol_sha256']==digest(HERE/protocol_file)
    assert protocol['predecessor_protocol_v2_sha256']==digest(HERE/'producer_protocol_v2.json')
    assert protocol['predecessor_source_v2_sha256']==digest(HERE/'produce_v2.py')
    for key,path in [('source',HERE/'produce_v3.py'),('hecke11',SOURCE/'tools/hecke11.py'),
                     ('selection',HERE/'selection.json'),('gate',HERE/'fiber_gate.json'),
                     ('conductor_diagnostic',HERE/'conductor_diagnostic.json'),
                     ('edge_diagnostic',HERE/'edge_diagnostic.json')]:
        assert protocol['source_sha256'][key]==digest(path)
    assert data['producer_protocol_sha256']==digest(HERE/'producer_protocol_v3.json')
    assert data['script_sha256']==digest(HERE/'produce.py')
    assert provenance['status']=='V3_SOURCE_HASH_FIELD_CORRECTED_BY_SIDECAR'
    assert provenance['full_matrix_v3_sha256']==digest(HERE/'full_matrix_v3.json')
    assert provenance['producer_protocol_v3_sha256']==digest(HERE/'producer_protocol_v3.json')
    assert provenance['reported_source_sha256']==data['script_sha256']
    assert provenance['executed_source_sha256']==protocol['source_sha256']['source']==digest(HERE/'produce_v3.py')
    assert cert['full_matrix_sha256']==digest(HERE/'full_matrix_v3.json')
    assert cert['script_sha256']==digest(HERE/'certify.py')
    assert diag['status']=='FIRST_PRIME_EXACT_CONDUCTOR_GATE_FAILED'
    assert diag['strata']['1']['actual_conductor_counts']=={'3':2}
    assert {r['j'] for r in diag['strata']['1']['rows']}=={193,1345}
    assert len(data['endomorphism_order_conductor_corrections'])==2
    assert bug['status']=='REPRODUCED_DISTINCT_ROOT_FLOOR_CLASSIFICATION_DISCREPANCY'
    assert bug['script_sha256']==digest(HERE/'sage_bug_receipt.py')
    assert {r['j'] for r in bug['records']}=={193,1345}
    assert all(len(r['phi3_roots'])==3 and sum(z['multiplicity'] for z in r['phi3_roots'])==4
               and r['explicit_isogeny_count']==4 and r['sage_height_above_floor_3']==0
               and r['sage_reported_endomorphism_conductor']==3 for r in bug['records'])
    assert {r['j'] for r in data['endomorphism_order_conductor_corrections']}=={193,1345}
    for correction in data['endomorphism_order_conductor_corrections']:
        assert (correction['reported_conductor'],correction['certified_conductor'],
                correction['explicit_degree3_isogeny_count'])==(3,1,4)
        edge=next(r for r in edges['rows'] if r['source_j']==correction['j'])
        assert len(edge['neighbors'])==3
        assert all(n['class_polynomial_memberships']==[2] for n in edge['neighbors'])
    points=data['column_points'];rows=data['relation_rows'];meta=data['row_records']
    assert (len(points),len(rows),len(meta))==(48,28,28)
    assert [r['column'] for r in points]==list(range(48))
    assert len({tuple(r['point']) for r in points})==48
    assert dict(Counter(str(r['conductor']) for r in points))=={'1':4,'2':12,'3':8,'6':24}
    assert dict(Counter((r['conductor'],r['degree']) for r in meta))=={
        (1,2):4,(1,3):4,(2,3):12,(3,2):8}
    assert data['rational_root_counts']=={'2':{'1':36,'3':12},'3':{'1':32,'4':16}}
    assert data['hecke_eigenvalues']=={'2':-2,'3':-1}
    c2_rows=[r['row'] for r in meta if r['conductor']==2 and r['degree']==3]
    row_for={(r['source'],r['degree']):r['row'] for r in meta}
    c2_columns={r['column'] for r in points if r['conductor']==2}
    c2_adjacency={}
    for source in c2_columns:
        counts=Counter({int(j):v for j,v in rows[row_for[(source,3)]].items()})
        counts[source]+=data['hecke_eigenvalues']['3']
        assert all(v>=0 for v in counts.values())
        neighbours=[j for j,n in counts.items() for _ in range(n)]
        assert len(neighbours)==4
        horizontal={j for j in neighbours if j in c2_columns}
        assert len(horizontal)==2 and len([j for j in neighbours if points[j]['conductor']==6])==2
        c2_adjacency[source]=horizontal
    assert all(source in c2_adjacency[j] for source,ns in c2_adjacency.items() for j in ns)
    unseen=set(c2_columns); c2_cycles=[]
    while unseen:
        stack=[min(unseen)];comp=set()
        while stack:
            x=stack.pop()
            if x not in comp:
                comp.add(x);stack.extend(c2_adjacency[x]-comp)
        unseen-=comp;c2_cycles.append(comp)
    assert sorted(map(len,c2_cycles))==[6,6]
    others=[i for i in range(28) if i not in c2_rows]
    nonfloor=[r['column'] for r in points if r['conductor']!=6]
    floor=[r['column'] for r in points if r['conductor']==6]
    assert len(c2_rows)==12 and len(others)==16 and len(nonfloor)==24 and len(floor)==24
    assert len(cert['local_commutator_relations'])==4
    c2_supports=[]
    for relation in cert['local_commutator_relations']:
        assert len(relation['c2_rows'])==3 and len(set(relation['c2_rows']))==3
        assert set(relation['c2_rows'])<=set(c2_rows)
        assert set(map(int,relation['other_terms']))<=set(others)
        left=combine(rows,{str(i):1 for i in relation['c2_rows']})
        right=combine(rows,relation['other_terms'])
        assert left==right
        c2_supports.extend(relation['c2_rows'])
    assert len(set(c2_supports))==12 and set(c2_supports)==set(c2_rows)
    basis=cert['projected_left_kernel_basis']
    assert len(basis)==8
    dense_basis=[[Fraction(v.get(str(i),0)) for i in range(28)] for v in basis]
    assert rank_fraction(dense_basis)==8
    images=[]
    for terms in basis:
        vector=combine(rows,terms)
        assert all(vector[j]==0 for j in nonfloor)
        images.append(vector)
    chosen=[]
    for record in cert['floor_only_vectors']:
        i=record['kernel_index'];assert 0<=i<8
        vector=images[i]
        expected=[Fraction(record['coordinates'].get(str(j),0)) for j in range(48)]
        assert vector==expected
        chosen.append([vector[j] for j in floor])
    assert len(chosen)==4 and rank_fraction(chosen)==4
    modular={}
    for q in (101,1000000007,2147483647):
        modular[str(q)]={'full':rank_mod(rows,list(range(48)),q),
                         'nonfloor':rank_mod(rows,nonfloor,q),
                         'others_full':rank_mod([rows[i] for i in others],list(range(48)),q),
                         'others_nonfloor':rank_mod([rows[i] for i in others],nonfloor,q),
                         'c2_full':rank_mod([rows[i] for i in c2_rows],list(range(48)),q),
                         'c2_nonfloor':rank_mod([rows[i] for i in c2_rows],nonfloor,q)}
        assert modular[str(q)]=={'full':24,'nonfloor':20,'others_full':16,
                                  'others_nonfloor':16,'c2_full':12,'c2_nonfloor':8}
    assert data['ranks']=={'full_QQ':24,'nonfloor_QQ':20,
                           'others_full_QQ':16,'others_nonfloor_QQ':16,
                           'c2_full_QQ':12,'c2_nonfloor_QQ':8,
                           'c2_increment_full_QQ':8,'c2_increment_nonfloor_QQ':4,
                           'floor_only_row_directions':4}
    out={'status':'PASS_INERT2_POSITIVE_INCREMENT_CERTIFIED',
         'selection_protocol_sha256':digest(HERE/'selection_protocol.json'),
         'producer_protocol_v3_sha256':digest(HERE/'producer_protocol_v3.json'),
         'full_matrix_sha256':digest(HERE/'full_matrix_v3.json'),
         'provenance_correction_sha256':digest(HERE/'provenance_correction.json'),
         'certificates_sha256':digest(HERE/'certificates.json'),
         'sage_bug_receipt_sha256':digest(HERE/'sage_bug_receipt.json'),
         'producer_failures_sha256':digest(HERE/'producer_failures.json'),
         'validator_sha256':digest(HERE/'validate.py'),
         'independent_modular_ranks':modular,
         'exact_local_relations':4,'independent_projected_kernel_vectors':8,
         'c2_degree3_horizontal_cycle_lengths':sorted(map(len,c2_cycles)),
         'independent_floor_only_vectors':4,
         'certified_ranks':data['ranks'],
         'candidate_id':None,'timing_claim':None}
    (HERE/'validation.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps({k:out[k] for k in ('status','exact_local_relations',
                                         'independent_projected_kernel_vectors','certified_ranks')},sort_keys=True))


if __name__=='__main__':main()
