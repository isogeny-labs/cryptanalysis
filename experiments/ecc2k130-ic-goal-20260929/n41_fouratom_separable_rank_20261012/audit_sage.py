"""Independent Sage coefficient construction and matrix-rank replay."""
import hashlib
import json
from pathlib import Path

from sage.all import GF, PolynomialRing, matrix

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
protocol=json.loads((HERE/'protocol.json').read_text())
result=json.loads((HERE/'result.json').read_text())
terms_path=ROOT/'n131_w15_rotated_fouratom_inverse_20261010/resultant.json'
panel_path=ROOT/'n41_symbolic_seed_fiber_20261012/panel.json'
assert hashlib.sha256(terms_path.read_bytes()).hexdigest()==protocol['sha256']['terms']
assert hashlib.sha256(panel_path.read_bytes()).hexdigest()==protocol['sha256']['panel']
terms=json.loads(terms_path.read_text())['terms']
panel=json.loads(panel_path.read_text())
R=PolynomialRing(GF(2),'t');t=R.gen()
F=GF(2**41,name='t',modulus=t**41+t**3+1)

def decode(x):
    return F(R([(x>>i)&1 for i in range(41)]))
def encode(x):
    return sum(int(bit)<<i for i,bit in enumerate(x.polynomial()))

checks=[]
fiber_ranks={}
for row in result['cases']:
    a,b,z=(decode(row[k]) for k in ('a','b','z'))
    aa=[a**i for i in range(9)]
    bb=[b**i for i in range(9)]
    zz=[z**i for i in range(9)]
    entries=[[F(0) for _ in range(9)] for _ in range(9)]
    for ea,eb,ep,eq,ez in terms:
        entries[ep][eq]+=aa[ea]*bb[eb]*zz[ez]
    M=matrix(F,entries)
    encoded=b''.join(encode(x).to_bytes(8,'little') for line in entries for x in line)
    assert hashlib.sha256(encoded).hexdigest()==row['matrix_sha256']
    assert M.rank()==row['rank']==9
    if row['case']=='positive':
        p,q=[decode(value) for value in row['source_products']]
        value=sum((entries[i][j]*p**i*q**j for i in range(9) for j in range(9)),F(0))
        assert value==0 and row['source_evaluation']==0
        expected=[(decode(mask[0]<<1)*decode(mask[1]<<1))**(2**rotation)
                  for mask,rotation in zip((group[0] for group in panel['ordered_masks']),panel['rotations'])]
        assert [p,q]==expected
    if row['case'] in ('positive','negative'):
        roots=[]
        for group,rotation in zip(panel['ordered_masks'],panel['rotations']):
            values=[(decode(mask[0]<<1)*decode(mask[1]<<1))**(2**rotation)
                    for mask in group]
            assert len(values)==len(set(values))==32
            roots.append(values)
        VP=matrix(F,[[p**i for i in range(9)] for p in roots[0]])
        VQ=matrix(F,[[q**j for j in range(9)] for q in roots[1]])
        fiber_rank=(VP*M*VQ.transpose()).rank()
        assert VP.rank()==VQ.rank()==fiber_rank==9
        fiber_ranks[row['case']]=int(fiber_rank)
    checks.append({'case':row['case'],'rank':int(M.rank()),
                   'matrix_sha256':row['matrix_sha256']})
out={'status':'PASS_INDEPENDENT_SAGE_RANK_REPLAY',
     'protocol_sha256':hashlib.sha256((HERE/'protocol.json').read_bytes()).hexdigest(),
     'result_sha256':hashlib.sha256((HERE/'result.json').read_bytes()).hexdigest(),
     'checked_cases':len(checks),'cases':checks,'positive_source_evaluation':0,
     'complete_32_by_32_fiber_ranks':fiber_ranks}
(HERE/'audit.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
print(out['status'],out['checked_cases'])
