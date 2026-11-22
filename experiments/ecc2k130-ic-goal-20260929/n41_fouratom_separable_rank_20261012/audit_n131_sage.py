"""Independent installed-Sage replay of N131 coefficient ranks."""
import hashlib,json
from pathlib import Path
from sage.all import GF,PolynomialRing,matrix
HERE=Path(__file__).resolve().parent
BASE=HERE.parent/'n131_w15_rotated_fouratom_inverse_20261010'
protocol=json.loads((HERE/'protocol_n131.json').read_text())
result=json.loads((HERE/'result_n131.json').read_text())
for name,path in [('terms',BASE/'resultant.json'),
                  ('positive',BASE/'input_n131_positive.txt'),
                  ('control',BASE/'input_n131_field_control.txt')]:
    assert hashlib.sha256(path.read_bytes()).hexdigest()==protocol['sha256'][name]
terms=json.loads((BASE/'resultant.json').read_text())['terms']
R=PolynomialRing(GF(2),'t');t=R.gen()
F=GF(2**131,name='t',modulus=t**131+t**13+t**2+t+1)
def dec(x):return F(R([(x>>i)&1 for i in range(131)]))
def enc(x):return sum(int(b)<<i for i,b in enumerate(x.polynomial()))
def chunks(items):return sum(int(x)<<(64*i) for i,x in enumerate(items))
checks=[]
for row in result['cases']:
    a,b,z=[dec(row[k]) for k in ('a','b','z')]
    matrix_rows=[[F(0) for _ in range(9)] for _ in range(9)]
    aa=[a**i for i in range(9)];bb=[b**i for i in range(9)];zz=[z**i for i in range(9)]
    for ia,ib,ip,iq,iz in terms:matrix_rows[ip][iq]+=aa[ia]*bb[ib]*zz[iz]
    M=matrix(F,matrix_rows)
    data=b''.join(enc(x).to_bytes(17,'little') for line in matrix_rows for x in line)
    assert hashlib.sha256(data).hexdigest()==row['matrix_sha256']
    assert M.rank()==row['rank']==9
    checks.append({'case':row['case'],'rank':int(M.rank()),'matrix_sha256':row['matrix_sha256']})
    if row['case']=='positive':
        native=json.loads((BASE/'native_n131_positive.json').read_text())
        p=dec(chunks(native['hits'][0]['p']))
        c0,c1=[dec(chunks(x)) for x in native['hits'][0]['gcd_coefficients']]
        q=c0/c1
        value=sum((matrix_rows[i][j]*p**i*q**j for i in range(9) for j in range(9)),F(0))
        assert value==0
out={'status':'PASS_INDEPENDENT_N131_SAGE_RANK_REPLAY','case_count':len(checks),
     'cases':checks,'positive_archived_product_evaluation':0,
     'result_sha256':hashlib.sha256((HERE/'result_n131.json').read_bytes()).hexdigest()}
(HERE/'audit_n131.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
print(out['status'],out['case_count'])
