"""Checked-Sage exact row-span and floor-direction certificates."""
from hashlib import sha256
import json
from pathlib import Path

from sage.all import QQ, matrix

HERE = Path(__file__).resolve().parent


def main():
    data_raw = (HERE/'full_matrix.json').read_bytes()
    data = json.loads(data_raw)
    assert data['status'] == 'FULL_D1199_RELATION_MATRIX_PRODUCED'
    rows = data['relation_rows']; metadata = data['row_records']
    c2 = [r['row'] for r in metadata if r['conductor']==2 and r['degree']==3]
    others = [i for i in range(len(rows)) if i not in set(c2)]
    nonfloor = [r['column'] for r in data['column_points'] if r['conductor']!=6]
    floor = [r['column'] for r in data['column_points'] if r['conductor']==6]
    assert (len(rows),len(c2),len(others),len(nonfloor),len(floor)) == (190,38,152,152,76)
    def dense(row_ids,cols):
        return matrix(QQ,[[rows[i].get(str(j),0) for j in cols] for i in row_ids])
    A = dense(others,list(range(228)))
    B = dense(c2,list(range(228)))
    Aproj = dense(others,nonfloor)
    assert A.rank()==152 and Aproj.rank()==150 and B.rank()==38
    coefficients = A.transpose().solve_right(B.transpose())
    assert A.transpose()*coefficients == B.transpose()
    kernel = Aproj.left_kernel().basis_matrix()
    assert kernel.nrows() == 2 and kernel.ncols() == 152
    assert kernel*Aproj == 0
    floor_vectors = kernel*A
    assert floor_vectors.rank()==2
    assert all(floor_vectors[:,j] == 0 for j in nonfloor)
    assert (kernel*A)[:,floor].rank()==2
    c2_witnesses = []
    for j,row_id in enumerate(c2):
        terms = {str(others[i]):str(coefficients[i,j]) for i in range(len(others))
                 if coefficients[i,j]}
        c2_witnesses.append({'row':row_id,'terms':terms})
    floor_witnesses = []
    for k in range(2):
        terms = {str(others[i]):str(kernel[k,i]) for i in range(len(others))
                 if kernel[k,i]}
        vector = {str(j):str(floor_vectors[k,j]) for j in floor if floor_vectors[k,j]}
        floor_witnesses.append({'terms':terms,'floor_vector':vector})
    out = {'status':'EXACT_ROW_SPAN_AND_FLOOR_CERTIFICATES',
           'full_matrix_sha256':sha256(data_raw).hexdigest(),
           'script_sha256':sha256((HERE/'certify.py').read_bytes()).hexdigest(),
           'c2_row_ids':c2,'other_row_ids':others,
           'nonfloor_column_ids':nonfloor,'floor_column_ids':floor,
           'c2_in_other_span_witnesses':c2_witnesses,
           'projected_other_kernel_witnesses':floor_witnesses,
           'c2_witness_nonzero_counts':[len(w['terms']) for w in c2_witnesses],
           'floor_witness_nonzero_counts':[len(w['terms']) for w in floor_witnesses],
           'candidate_id':None,'timing_claim':None}
    (HERE/'certificates.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'status':out['status'],
                      'c2_witness_nonzero_counts':out['c2_witness_nonzero_counts'],
                      'floor_witness_nonzero_counts':out['floor_witness_nonzero_counts']},sort_keys=True))


if __name__=='__main__':
    main()
