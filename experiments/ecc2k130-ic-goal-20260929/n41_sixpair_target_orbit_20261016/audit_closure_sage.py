"""Enumerate the actual signed-Frobenius projected N41 source closure."""
import hashlib
import json
from pathlib import Path
from sage.all import GF, PolynomialRing, EllipticCurve

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
protocol=json.loads((HERE/'closure_protocol.json').read_text())
for path,digest in protocol['sources'].items():assert sha(path)==digest,path
g=json.loads((ROOT/'n41_w8_fixed_sum_table_20261009/geometry.json').read_text())
s=json.loads((ROOT/'n41_w7_entropy_cubic_20261011/w8/geometry.json').read_text())
rows={row['mask']:row for row in s['rows']}
R=PolynomialRing(GF(2),'t');t=R.gen()
F=GF(2**41,'t',modulus=t**41+t**3+1)
E=EllipticCurve(F,[1,0,0,0,1])
def dec(word):return F(R([(int(word)>>i)&1 for i in range(41)]))
def enc(v):return sum(int(b)<<i for i,b in enumerate(v.polynomial().list()))
allowed={mask for a in g['permitted_canonical_a'] for mask in (a,a^g['fixed_seed_sum_code'])}
base={}
for mask in allowed:
    row=rows[mask];base.setdefault(row['column'],E(dec(row['projected_point'][0]),dec(row['projected_point'][1])))
assert len(base)==g['folded_columns_K']==77
closure=set()
for P in base.values():
    orbit=set();Q=P
    for _ in range(41):
        for T in (Q,-Q):orbit.add((enc(T[0]),enc(T[1])))
        Q=E(Q[0]**2,Q[1]**2)
    assert Q==P and len(orbit)==82 and not closure.intersection(orbit)
    closure.update(orbit)
assert len(closure)==77*82
out={'status':'PASS_N41_SIGNED_FROBENIUS_CLOSURE','folded_columns':77,
     'points_per_column':82,'actual_usable_projected_points_B':len(closure),
     'protocol_sha256':sha(HERE/'closure_protocol.json')}
(HERE/'closure_audit.json').write_text(json.dumps(out,sort_keys=True,indent=2)+'\n')
print(out['status'],out['actual_usable_projected_points_B'])
