"""Complete N41 three-code box join through reusable reciprocal pair sums."""
import hashlib
import json
import resource
import time
from pathlib import Path

from sage.all import EllipticCurve, GF, PolynomialRing

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SOURCE = ROOT/'n41_n131_w29_rotation_alignment_20261017/aligned_states.json'
RELATION = ROOT/'n41_n131_w29_rotation_alignment_20261017/n41_audit_result.json'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def digest_rows(rows):
    return hashlib.sha256(json.dumps(rows, separators=(',', ':')).encode()).hexdigest()


protocol = json.loads((HERE/'full_protocol.json').read_text())
for name, path in {'script':Path(__file__), 'runtime':HERE/'full_sage_runtime_info.json',
                   'states':SOURCE, 'relation':RELATION,
                   'panel':HERE/'panel.json'}.items():
    assert sha(path) == protocol['source_sha256'][name], name
assert not (HERE/'full_result.json').exists()
source = json.loads(SOURCE.read_text())
panel = json.loads((HERE/'panel.json').read_text())
assert source['usable_edges'] == 71
assert panel['fixed_slot_state_ids'] == {'0':105,'4':111}

R = PolynomialRing(GF(2),'u')
u = R.gen()
F = GF(2**41,name='u',modulus=u**41+u**3+1)
E = EllipticCurve(F,[1,0,0,0,1])


def dec(word):
    return F(R([(int(word)>>i)&1 for i in range(41)]))


def enc(value):
    return sum(int(c)<<i for i,c in enumerate(value.polynomial().list()))


def halftrace(value):
    original=value
    out=F.zero()
    for _ in range(21):
        out+=value
        value=value**4
    assert out**2+out==original
    return out


def roots(a,b):
    if not a or not b:
        return [],True
    A=1+(a*b)**2
    B=a*b
    D=a**2+b**2
    if not A:
        return [D/B],True
    rhs=A*D/(B**2)
    if rhs.trace():
        return [],False
    h=halftrace(rhs)
    scale=B/A
    return [scale*h,scale*(h+1)],False


states=[[E(dec(row['point'][0]),dec(row['point'][1])) for row in slot]
        for slot in source['states']]
raw=E(dec(source['target_raw_point'][0]),dec(source['target_raw_point'][1]))
public=E(raw[0]**(1<<6),raw[1]**(1<<6))
fixed0=states[0][105]
fixed4=states[4][111]
fixed_columns=set(source['states'][0][105]['columns']+
                  source['states'][4][111]['columns'])
columns=[[set(source['states'][slot][4*c]['columns']) for c in range(71)]
         for slot in range(5)]

setup_tick=time.monotonic()
root_pairs={slot:[] for slot in (1,2,3)}
for slot in (1,2,3):
    for code in range(71):
        words=sorted({enc(1/states[slot][sid][0])
                      for sid in range(4*code,4*code+4)})
        assert len(words)==2
        root_pairs[slot].append([dec(word) for word in words])

left_rows=[]
index={}
exception_pairs=[]
source_eligible_pairs=0
for c1 in range(71):
    if columns[1][c1]&fixed_columns:
        continue
    for c2 in range(71):
        joined=columns[1][c1]|columns[2][c2]|fixed_columns
        if len(joined)!=8:
            continue
        source_eligible_pairs+=1
        values=set()
        exceptional=False
        for a in root_pairs[1][c1]:
            for b in root_pairs[2][c2]:
                rr,exc=roots(a,b)
                exceptional |= exc or any(not v for v in rr)
                values.update(enc(v) for v in rr if v)
        if exceptional:
            exception_pairs.append([c1,c2])
        for word in values:
            index.setdefault(word,[]).append((c1,c2))
        left_rows.append([c1,c2,sorted(values),exceptional])
setup_seconds=time.monotonic()-setup_tick

query_tick=time.monotonic()
target=public-fixed0-fixed4
assert target!=E(0) and target[0]
t=1/target[0]
right_rows=[]
candidate=set()
right_exceptions=[]
for c3 in range(71):
    if columns[3][c3]&fixed_columns:
        continue
    values=set()
    exceptional=False
    for c in root_pairs[3][c3]:
        rr,exc=roots(c,t)
        exceptional |= exc or any(not v for v in rr)
        values.update(enc(v) for v in rr if v)
    if exceptional:
        right_exceptions.append(c3)
    right_rows.append([c3,sorted(values),exceptional])
    for word in values:
        for c1,c2 in index.get(word,[]):
            allcols=columns[1][c1]|columns[2][c2]|columns[3][c3]|fixed_columns
            if len(allcols)==10:
                candidate.add((c1,c2,c3))

eligible_boxes=0
for c1,c2,_,_ in left_rows:
    pre=columns[1][c1]|columns[2][c2]|fixed_columns
    for c3 in range(71):
        if len(pre|columns[3][c3])==10:
            eligible_boxes+=1

exact=[]
for c1,c2,c3 in sorted(candidate):
    for i in range(4*c1,4*c1+4):
        for j in range(4*c2,4*c2+4):
            ij=states[1][i]+states[2][j]
            for k in range(4*c3,4*c3+4):
                if ij+states[3][k]==target:
                    exact.append([c1,c2,c3,i,j,k])
assert [61,16,11,244,66,47] in exact
query_seconds=time.monotonic()-query_tick

result={
    'status':'PASS_N41_FULL_THREE_CODE_FAMILY_S3_INDEX',
    'candidate_id':None, 'curve_id':source['curve_id'],
    'source_code_count':71, 'source_eligible_pair_families':source_eligible_pairs,
    'source_eligible_triple_boxes':eligible_boxes,
    'left_coordinate_records':sum(len(row[2]) for row in left_rows),
    'distinct_left_coordinates':len(index),
    'right_code_families':len(right_rows),
    'candidate_code_boxes':[list(v) for v in sorted(candidate)],
    'exact_state_witnesses':exact,
    'exception_pair_count':len(exception_pairs),
    'exception_pairs':exception_pairs,
    'right_exception_count':len(right_exceptions),
    'right_exceptions':right_exceptions,
    'left_digest':digest_rows(left_rows),
    'right_digest':digest_rows(right_rows),
    'target_partial_point':[enc(target[0]),enc(target[1])],
    'target_reciprocal':enc(t),
    'setup_seconds':setup_seconds, 'query_seconds':query_seconds,
    'self_maxrss_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
    'protocol_sha256':sha(HERE/'full_protocol.json'),
    'source_sha256':{'script':sha(Path(__file__)),
                     'runtime':sha(HERE/'full_sage_runtime_info.json'),
                     'states':sha(SOURCE),'panel':sha(HERE/'panel.json')},
}
(HERE/'full_result.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
print(json.dumps({k:result[k] for k in
                  ('status','source_eligible_pair_families',
                   'source_eligible_triple_boxes','left_coordinate_records',
                   'distinct_left_coordinates','right_code_families',
                   'candidate_code_boxes','exact_state_witnesses',
                   'exception_pair_count','right_exception_count',
                   'setup_seconds','query_seconds')}))
