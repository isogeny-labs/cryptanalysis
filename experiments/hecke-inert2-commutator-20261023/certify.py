"""Exact local commutator and projected-kernel certificates for D=-35."""
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path

from sage.all import QQ,matrix

HERE=Path(__file__).resolve().parent


def main():
    raw=(HERE/'full_matrix_v3.json').read_bytes();data=json.loads(raw)
    assert data['status']=='INERT2_MULTIPLICITY_AWARE_FULL_MATRIX_PRODUCED'
    rows=data['relation_rows'];meta=data['row_records'];points=data['column_points']
    assert (len(rows),len(points))==(28,48)
    row_for={(m['source'],m['degree']):m['row'] for m in meta}
    assert len(row_for)==28
    c1=[r['column'] for r in points if r['conductor']==1]
    c2={r['column'] for r in points if r['conductor']==2}
    local=[]
    def neighbours(source,degree):
        r=rows[row_for[(source,degree)]]
        counts={int(k):v for k,v in r.items()}
        counts[source]=counts.get(source,0)+data['hecke_eigenvalues'][str(degree)]
        assert all(v>=0 for v in counts.values())
        return [j for j,n in counts.items() for _ in range(n)]
    for source in c1:
        n2,n3=neighbours(source,2),neighbours(source,3)
        assert len(n2)==3 and set(n2)<=c2 and len(set(n2))==3
        assert len(n3)==4
        c2_rows=[row_for[(q,3)] for q in n2]
        other_terms=Counter(row_for[(w,2)] for w in n3)
        other_terms[row_for[(source,2)]]+=1
        other_terms[row_for[(source,3)]]-=2
        other_terms={k:v for k,v in other_terms.items() if v}
        left=Counter()
        for row_id in c2_rows:
            for col,v in rows[row_id].items():left[int(col)]+=v
        right=Counter()
        for row_id,coeff in other_terms.items():
            for col,v in rows[row_id].items():right[int(col)]+=coeff*v
        assert {k:v for k,v in left.items() if v}=={k:v for k,v in right.items() if v}
        local.append({'c1_source':source,'c2_columns':n2,'c2_rows':c2_rows,
                      'other_terms':{str(k):v for k,v in sorted(other_terms.items())}})
    assert len(local)==4 and len({q for rec in local for q in rec['c2_columns']})==12
    full=matrix(QQ,[[r.get(str(j),0) for j in range(48)] for r in rows])
    nonfloor=[r['column'] for r in points if r['conductor']!=6]
    floor=[r['column'] for r in points if r['conductor']==6]
    projected=full[:,nonfloor]
    assert full.rank()==24 and projected.rank()==20
    kernel=projected.left_kernel().basis_matrix()
    assert kernel.nrows()==8 and kernel.ncols()==28 and kernel*projected==0
    images=kernel*full
    assert images.rank()==4 and all(images[:,j]==0 for j in nonfloor)
    chosen=[]
    for i in range(8):
        trial=chosen+[i]
        if images[trial,:].rank()>len(chosen):chosen=trial
        if len(chosen)==4:break
    assert len(chosen)==4
    kernel_rows=[{str(j):str(kernel[i,j]) for j in range(28) if kernel[i,j]}
                 for i in range(8)]
    floor_vectors=[{'kernel_index':i,
                    'coordinates':{str(j):str(images[i,j]) for j in floor if images[i,j]}}
                   for i in chosen]
    out={'status':'INERT2_EXACT_COMMUTATOR_AND_PROJECTION_CERTIFICATES',
         'full_matrix_sha256':sha256(raw).hexdigest(),
         'script_sha256':sha256((HERE/'certify.py').read_bytes()).hexdigest(),
         'local_commutator_relations':local,
         'projected_left_kernel_basis':kernel_rows,
         'floor_only_vectors':floor_vectors,
         'candidate_id':None,'timing_claim':None}
    (HERE/'certificates.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'status':out['status'],'local_relations':len(local),
                      'projected_kernel_basis':len(kernel_rows),
                      'floor_only_vectors':len(floor_vectors)},sort_keys=True))


if __name__=='__main__':main()
