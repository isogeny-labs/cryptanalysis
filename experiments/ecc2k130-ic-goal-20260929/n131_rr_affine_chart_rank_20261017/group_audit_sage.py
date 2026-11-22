"""Direct curve addition for all affine-chart sign assignments."""
import hashlib
import json
import resource
import signal
import time
from pathlib import Path
from sage.all import EllipticCurve, GF, PolynomialRing

D=Path(__file__).resolve().parent
sha=lambda path:hashlib.sha256(Path(path).read_bytes()).hexdigest()
p=json.loads((D/'group_protocol.json').read_text())
assert sha(D/'group_audit_sage.py')==p['group_audit_source_sha256']
assert sha(D/'panel.json')==p['panel_sha256']
assert sha(D/'result.json')==p['rank_result_sha256']
assert sha(D/'audit_result.json')==p['determinant_audit_sha256']
signal.alarm(p['wall_cap_s'])
start=time.monotonic()
panel=json.loads((D/'panel.json').read_text())
result=json.loads((D/'result.json').read_text())
R=PolynomialRing(GF(2),'t');t=R.gen()
F=GF(2**131,name='t',modulus=t**131+t**13+t**2+t+1)
E=EllipticCurve(F,[1,0,0,0,1])
def dec(word):return F(R([(int(word)>>i)&1 for i in range(131)]))
def point(row):return E(*map(dec,row))
target=point(panel['target'])
fixed=[point(row) for row in panel['fixed_points']]
rows=[]
for code,roots in enumerate(panel['selection']['roots']):
    for root in (0,1):
        P=point(roots[root][0])
        points=[P]+fixed
        matches=[]
        for sign in range(64):
            total=E(0)
            for i,Q in enumerate(points):
                total+=-Q if (sign>>i)&1 else Q
            if total==target:matches.append(sign)
        expected=result['rows'][2*code+root]['determinant_zero_sign_masks']
        assert matches==expected
        rows.append({'code':code,'root':root,'group_matches':matches})
record={'status':'PASS_INDEPENDENT_N131_AFFINE_GROUP_REPLAY',
        'rows':rows,'total_signs_checked':512,
        'wall_s':time.monotonic()-start,
        'self_peak_rss_bytes_darwin':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        'group_protocol_sha256':sha(D/'group_protocol.json')}
with (D/'group_audit_result.json').open('x') as out:
    json.dump(record,out,sort_keys=True,indent=2);out.write('\n')
print(record['status'])
