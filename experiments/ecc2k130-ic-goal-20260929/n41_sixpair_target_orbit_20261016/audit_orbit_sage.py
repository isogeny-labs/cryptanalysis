"""Independently replay every raw and subgroup Frobenius target orbit point."""
import hashlib
import json
from pathlib import Path
from sage.all import GF, PolynomialRing, EllipticCurve

HERE=Path(__file__).resolve().parent
record=json.loads((HERE/'protocol.json').read_text())
build=json.loads((HERE/'build_result.json').read_text())
R=PolynomialRing(GF(2),'t');t=R.gen()
F=GF(2**41,'t',modulus=t**41+t**3+1)
E=EllipticCurve(F,[1,0,0,0,1])
def dec(word):return F(R([(int(word)>>i)&1 for i in range(41)]))
def enc(value):return sum(int(bit)<<i for i,bit in enumerate(value.polynomial().list()))
def point(pair):return E(dec(pair[0]),dec(pair[1]))
def phi(p):return E(p[0]**2,p[1]**2)
raw=point(record['public_raw_point'])
public=point(record['public_subgroup_point'])
assert 4*raw==public
panel=next(p for p in build['panels'] if p['name']=='public')
assert panel['orbit_size']==41
orbit=[];current=raw;expected=public
for j in range(41):
    assert 4*current==expected
    reciprocal=1/current[0]
    assert enc(reciprocal)==panel['target_orbit'][j]
    restored=current
    for _ in range((41-j)%41):restored=phi(restored)
    assert restored==raw
    orbit.append([enc(current[0]),enc(current[1])])
    current=phi(current)
    expected=phi(expected)
assert current==raw and expected==public and len({tuple(p) for p in orbit})==41
audit={'status':'PASS_N41_FROBENIUS_TARGET_ORBIT','raw_orbit_size':41,
       'public_raw_point':record['public_raw_point'],
       'public_subgroup_point':record['public_subgroup_point'],
       'protocol_sha256':hashlib.sha256((HERE/'protocol.json').read_bytes()).hexdigest(),
       'build_sha256':hashlib.sha256((HERE/'build_result.json').read_bytes()).hexdigest(),
       'orbit_points':orbit}
(HERE/'orbit_audit.json').write_text(json.dumps(audit,sort_keys=True,indent=2)+'\n')
print(audit['status'])
