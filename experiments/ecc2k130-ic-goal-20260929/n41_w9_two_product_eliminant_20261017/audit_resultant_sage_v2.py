"""Independent nested resultant reconstruction of the two-product polynomial."""
import hashlib
import json
import resource
import time
from pathlib import Path

from sage.all import GF, PolynomialRing

HERE=Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


protocol=json.loads((HERE/'resultant_audit_protocol_v2.json').read_text())
for key,path in {'script':Path(__file__),'runtime':HERE/'resultant_audit_runtime_info_v2.json',
                 'producer':HERE/'result.json'}.items():
    assert sha(path)==protocol['source_sha256'][key],key
assert not (HERE/'resultant_audit_result_v2.json').exists()
producer=json.loads((HERE/'result.json').read_text())

K=PolynomialRing(GF(2),'u')
u=K.gen()
F=GF(2**41,name='u',modulus=u**41+u**3+1)


def dec(word):
    return F(K([(int(word)>>i)&1 for i in range(41)]))


def enc(value):
    return sum(int(c)<<i for i,c in enumerate(value.polynomial().list()))


constants=producer['pair_equation_constants']
C1,H1,C2,H2=(dec(constants[key]) for key in ('C1','H1','C2','H2'))
t=dec(producer['target_reciprocal'])
start=time.monotonic()
PQ=PolynomialRing(F,names=('p','q'))
p,q=PQ.gens()
A=PolynomialRing(PQ,'a')
a=A.gen()
B=PolynomialRing(A,'b')
b=B.gen()
f1=C1*a*a+p*a+H1
f2=C2*b*b+q*b+H2
s3=(a*b*t)*(a*b*t)+a*b*t+a*a+b*b+t*t
first=f2.resultant(s3)
assert first.degree()==4
second=f1.resultant(first)
assert second
normalized=second/(C1**3)
terms=[[list(monomial),enc(coefficient)]
       for monomial,coefficient in sorted(normalized.dict().items())]
assert terms==producer['eliminant_terms']
result={
    'status':'PASS_INDEPENDENT_N41_NESTED_RESULTANT_COEFFICIENTS',
    'first_resultant_degree_a':int(first.degree()),
    'final_term_count':len(terms),
    'normalized_by_C1_power':3,
    'all_coefficients_equal':True,
    'elapsed_seconds':time.monotonic()-start,
    'self_maxrss_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
    'protocol_sha256':sha(HERE/'resultant_audit_protocol_v2.json'),
    'producer_sha256':sha(HERE/'result.json'),
}
(HERE/'resultant_audit_result_v2.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
print(json.dumps({key:result[key] for key in
                  ('status','first_resultant_degree_a','final_term_count',
                   'all_coefficients_equal','elapsed_seconds')}))
