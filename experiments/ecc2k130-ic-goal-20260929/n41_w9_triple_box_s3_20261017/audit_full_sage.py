"""Independent complete group-sum index for the full N41 code domain."""
import hashlib
import json
import resource
import time
from pathlib import Path

from sage.all import EllipticCurve, GF, PolynomialRing

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
SOURCE=ROOT/'n41_n131_w29_rotation_alignment_20261017/aligned_states.json'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def digest_rows(rows):
    return hashlib.sha256(json.dumps(rows,separators=(',',':')).encode()).hexdigest()


protocol=json.loads((HERE/'full_audit_protocol.json').read_text())
for name,path in {'script':Path(__file__),'runtime':HERE/'full_audit_runtime_info.json',
                  'states':SOURCE,'producer':HERE/'full_result.json',
                  'producer_protocol':HERE/'full_protocol.json'}.items():
    assert sha(path)==protocol['source_sha256'][name],name
assert not (HERE/'full_audit_result.json').exists()
source=json.loads(SOURCE.read_text())
producer=json.loads((HERE/'full_result.json').read_text())
assert producer['status']=='PASS_N41_FULL_THREE_CODE_FAMILY_S3_INDEX'

R=PolynomialRing(GF(2),'u')
u=R.gen()
F=GF(2**41,name='u',modulus=u**41+u**3+1)
E=EllipticCurve(F,[1,0,0,0,1])


def dec(word):
    return F(R([(int(word)>>i)&1 for i in range(41)]))


def enc(value):
    return sum(int(c)<<i for i,c in enumerate(value.polynomial().list()))


states=[[E(dec(row['point'][0]),dec(row['point'][1])) for row in slot]
        for slot in source['states']]
raw=E(dec(source['target_raw_point'][0]),dec(source['target_raw_point'][1]))
public=E(raw[0]**(1<<6),raw[1]**(1<<6))
target=public-states[0][105]-states[4][111]
assert target!=E(0) and target[0]
assert producer['target_partial_point']==[enc(target[0]),enc(target[1])]
columns=[[set(source['states'][slot][4*c]['columns']) for c in range(71)]
         for slot in range(5)]
fixedcols=set(source['states'][0][105]['columns']+
              source['states'][4][111]['columns'])

start=time.monotonic()
left_rows=[]
left_index={}
point_index={}
group_chart_exceptions=0
for c1 in range(71):
    if columns[1][c1]&fixedcols:
        continue
    for c2 in range(71):
        cols=fixedcols|columns[1][c1]|columns[2][c2]
        if len(cols)!=8:
            continue
        words=set()
        for i in range(4*c1,4*c1+4):
            for j in range(4*c2,4*c2+4):
                point=states[1][i]+states[2][j]
                if point==E(0) or not point[0]:
                    group_chart_exceptions+=1
                    continue
                word=enc(1/point[0])
                words.add(word)
                point_index.setdefault((c1,c2),[]).append((i,j,point))
        for word in words:
            left_index.setdefault(word,[]).append((c1,c2))
        left_rows.append([c1,c2,sorted(words),False])

right_rows=[]
right_points={}
candidate=set()
for c3 in range(71):
    if columns[3][c3]&fixedcols:
        continue
    words=set()
    right_points[c3]=[]
    for k in range(4*c3,4*c3+4):
        point=target-states[3][k]
        if point==E(0) or not point[0]:
            group_chart_exceptions+=1
            continue
        word=enc(1/point[0])
        words.add(word)
        right_points[c3].append((k,point))
    right_rows.append([c3,sorted(words),False])
    for word in words:
        for c1,c2 in left_index.get(word,[]):
            cols=fixedcols|columns[1][c1]|columns[2][c2]|columns[3][c3]
            if len(cols)==10:
                candidate.add((c1,c2,c3))

eligible=0
for c1,c2,_,_ in left_rows:
    pre=fixedcols|columns[1][c1]|columns[2][c2]
    eligible+=sum(len(pre|columns[3][c3])==10 for c3 in range(71))

exact=[]
for c1,c2,c3 in sorted(candidate):
    for i,j,point in point_index[(c1,c2)]:
        for k,remaining in right_points[c3]:
            if point==remaining:
                assert states[0][105]+states[1][i]+states[2][j]+states[3][k]+states[4][111]==public
                exact.append([c1,c2,c3,i,j,k])

assert group_chart_exceptions==0
assert len(left_rows)==producer['source_eligible_pair_families']==4686
assert eligible==producer['source_eligible_triple_boxes']==313158
assert sum(len(row[2]) for row in left_rows)==producer['left_coordinate_records']==37488
assert len(left_index)==producer['distinct_left_coordinates']==37488
assert len(right_rows)==producer['right_code_families']==69
assert digest_rows(left_rows)==producer['left_digest']
assert digest_rows(right_rows)==producer['right_digest']
assert [list(v) for v in sorted(candidate)]==producer['candidate_code_boxes']
assert sorted(exact)==producer['exact_state_witnesses']

result={
    'status':'PASS_INDEPENDENT_N41_FULL_THREE_CODE_GROUP_INDEX',
    'source_eligible_pair_families':len(left_rows),
    'source_eligible_triple_boxes':eligible,
    'left_coordinate_records':sum(len(row[2]) for row in left_rows),
    'right_code_families':len(right_rows),
    'candidate_code_boxes':[list(v) for v in sorted(candidate)],
    'exact_state_witnesses':sorted(exact),
    'group_chart_exceptions':group_chart_exceptions,
    'left_digest':digest_rows(left_rows),'right_digest':digest_rows(right_rows),
    'elapsed_seconds':time.monotonic()-start,
    'self_maxrss_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
    'protocol_sha256':sha(HERE/'full_audit_protocol.json'),
    'source_sha256':{'producer':sha(HERE/'full_result.json'),
                     'states':sha(SOURCE)},
}
(HERE/'full_audit_result.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
print(json.dumps({k:result[k] for k in
                  ('status','source_eligible_pair_families',
                   'source_eligible_triple_boxes','candidate_code_boxes',
                   'exact_state_witnesses','group_chart_exceptions')}))
