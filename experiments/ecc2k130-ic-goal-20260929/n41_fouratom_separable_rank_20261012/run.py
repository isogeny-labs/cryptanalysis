"""Exact coefficient-matrix ranks for the frozen rotated four-atom eliminant."""
import hashlib
import json
import random
import resource
import time
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
TERMS=ROOT/'n131_w15_rotated_fouratom_inverse_20261010/resultant.json'
PANEL=ROOT/'n41_symbolic_seed_fiber_20261012/panel.json'
MOD=(1<<41)|(1<<3)|1
MASK=(1<<41)-1

def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def mul(a,b):
    out=0
    while b:
        if b&1:out^=a
        b>>=1;a<<=1
        if a>>41:a^=MOD
    return out
def power(a,k):
    out=1
    while k:
        if k&1:out=mul(out,a)
        a=mul(a,a);k>>=1
    return out
def frob(a,k):
    for _ in range(k):a=mul(a,a)
    return a
def coefficients(terms,a,b,z):
    aa=[power(a,i) for i in range(9)]
    bb=[power(b,i) for i in range(9)]
    zz=[power(z,i) for i in range(9)]
    matrix=[[0]*9 for _ in range(9)]
    for ea,eb,ep,eq,ez in terms:
        matrix[ep][eq]^=mul(mul(aa[ea],bb[eb]),zz[ez])
    return matrix
def rank_and_pivots(input_matrix):
    rows=[row[:] for row in input_matrix]
    pivots=[];rank=0
    for column in range(9):
        pivot=next((i for i in range(rank,9) if rows[i][column]),None)
        if pivot is None:continue
        rows[rank],rows[pivot]=rows[pivot],rows[rank]
        value=rows[rank][column]
        pivots.append([column,value])
        inv=power(value,(1<<41)-2)
        assert mul(value,inv)==1
        rows[rank]=[mul(x,inv) for x in rows[rank]]
        for i in range(rank+1,9):
            value=rows[i][column]
            if value:rows[i]=[x^mul(value,y) for x,y in zip(rows[i],rows[rank])]
        rank+=1
    return rank,pivots
def evaluate(matrix,p,q):
    pp=[power(p,i) for i in range(9)]
    qq=[power(q,i) for i in range(9)]
    value=0
    for i in range(9):
        for j in range(9):
            value^=mul(matrix[i][j],mul(pp[i],qq[j]))
    return value

def main():
    start=time.monotonic_ns()
    protocol=json.loads((HERE/'protocol.json').read_text())
    for path,expected in ((TERMS,protocol['sha256']['terms']),
                          (PANEL,protocol['sha256']['panel']),
                          (Path(__file__),protocol['sha256']['producer'])):
        assert digest(path)==expected,path
    terms=json.loads(TERMS.read_text())['terms']
    assert len(terms)==266
    panel=json.loads(PANEL.read_text())
    a,b=[frob(s<<1,r) for s,r in zip(panel['seeds'],panel['rotations'])]
    rng=random.Random(protocol['random_seed'])
    cases=[('positive',a,b,panel['positive_reciprocal']),
           ('negative',a,b,panel['negative_reciprocal'])]
    for i in range(protocol['random_cases']):
        sa=rng.randrange(1,256);sb=rng.randrange(1,256)
        cases.append((f'random_{i}',frob(sa<<1,14),frob(sb<<1,21),rng.randrange(1,1<<41)))
    output=[]
    for name,aa,bb,z in cases:
        matrix=coefficients(terms,aa,bb,z)
        rank,pivots=rank_and_pivots(matrix)
        encoded=b''.join(x.to_bytes(8,'little') for row in matrix for x in row)
        row={'case':name,'a':aa,'b':bb,'z':z,'rank':rank,'pivots':pivots,
             'nonzero_coefficients':sum(bool(x) for r in matrix for x in r),
             'matrix_sha256':hashlib.sha256(encoded).hexdigest()}
        if name=='positive':
            p,q=[frob(mul(mask[0]<<1,mask[1]<<1),r) for mask,r in
                 zip((group[0] for group in panel['ordered_masks']),panel['rotations'])]
            row['source_products']=[p,q]
            row['source_evaluation']=evaluate(matrix,p,q)
            assert row['source_evaluation']==0
        output.append(row)
    result={'status':'EXACT_COEFFICIENT_RANK_CENSUS','candidate_id':None,
            'protocol_sha256':digest(HERE/'protocol.json'),
            'case_count':len(output),'ranks':{r['case']:r['rank'] for r in output},
            'cases':output,'elapsed_ns_exploratory':time.monotonic_ns()-start,
            'peak_rss_bytes_macos':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
    (HERE/'result.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'status':result['status'],'case_count':len(output),
                      'rank_histogram':{str(i):sum(r['rank']==i for r in output)
                                        for i in range(10) if any(r['rank']==i for r in output)}}))
if __name__=='__main__':main()
