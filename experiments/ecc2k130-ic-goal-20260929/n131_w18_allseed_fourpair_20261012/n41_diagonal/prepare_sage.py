"""Export every exact signed W8 all-seed pair at four Frobenius rotations."""
import hashlib
import json
from pathlib import Path
from sage.all import EllipticCurve, GF, PolynomialRing

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
BASE = ROOT / 'n41_w7_entropy_cubic_20261011/w8'
protocol = json.loads((HERE / 'prepare_protocol.json').read_text())
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
for key,path in {'source':Path(__file__),'geometry':BASE/'geometry.json',
                 'fixture':BASE/'fixture.json','sage_runtime':HERE/'sage_runtime_info.json'}.items():
    assert sha(path) == protocol['sha256'][key]
assert not (HERE/'pairs.tsv').exists()
geo = json.loads((BASE/'geometry.json').read_text())
fixture = json.loads((BASE/'fixture.json').read_text())
ring = PolynomialRing(GF(2),'t'); t=ring.gen()
field = GF(2**41,name='t',modulus=t**41+t**3+1)
curve = EllipticCurve(field,[1,0,0,0,1])
def dec(n): return field(ring([(int(n)>>i)&1 for i in range(41)]))
def enc(v): return sum(int(bit)<<i for i,bit in enumerate(v.polynomial().list()))
rows = {int(r['mask']):r for r in geo['rows']}
raw = {m:curve(*map(dec,r['raw_point'])) for m,r in rows.items()}
diagonal = {m:raw[m]+curve(raw[m][0]**2,raw[m][1]**2) for m in raw}
assert len(diagonal)==125
for mask,P in diagonal.items():
    assert P != curve(0) and P[0] == 1/dec(mask<<1)
rotations=(0,7,14,21)
count=0; skipped=0
with (HERE/'pairs.tsv').open('x') as out:
    out.write('ECC2K41_ALLSEED4 4 4\n')
    for j,xy in enumerate(fixture['raw_target_preimages']):
        out.write(f'T {j} {xy[0]} {xy[1]}\n')
    for slot,rotation in enumerate(rotations):
        sid=0
        for a in sorted(rows):
            for b in sorted(rows):
                if a>=b or rows[a]['column']==rows[b]['column']: continue
                for sign_a in (0,1):
                    for sign_b in (0,1):
                        P=(-diagonal[a] if sign_a else diagonal[a])+(-diagonal[b] if sign_b else diagonal[b])
                        if P==curve(0) or P[0]==0:
                            skipped+=1;continue
                        P=curve(P[0]**(1<<rotation),P[1]**(1<<rotation))
                        out.write(f'S {slot} {sid} {a} {b} {rows[a]["column"]} {rows[b]["column"]} {sign_a} {sign_b} {enc(P[0])} {enc(P[1])}\n')
                        sid+=1
        assert sid>0
        count+=sid
        print('SLOT',slot,sid,flush=True)
result={'status':'PASS_N41_DIAGONAL_ALLSEED_PAIR_EXPORT','pair_rows_total':count,'skipped_exceptional':skipped,
        'pairs_per_slot':count//4,'output_sha256':sha(HERE/'pairs.tsv'),
        'protocol_sha256':sha(HERE/'prepare_protocol.json')}
(HERE/'prepare_result.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
print(result)
