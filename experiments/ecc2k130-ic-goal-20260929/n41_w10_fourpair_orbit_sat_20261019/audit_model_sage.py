"""Independently lift an unpinned SAT model to the frozen N41 public point."""
import hashlib
import itertools
import json
import resource
import signal
import time
from pathlib import Path
from sage.all import EllipticCurve,GF,PolynomialRing

import circuit
from build_control import check_assignment

HERE=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
cfg=json.loads((HERE/'audit_protocol.json').read_text())
assert cfg['status']=='FROZEN_BEFORE_N41_W10_SAT_MODEL_AUDIT'
for rec in cfg['sources'].values():assert sha(rec['path'])==rec['sha256']
signal.signal(signal.SIGALRM,lambda *_:(_ for _ in ()).throw(TimeoutError('model audit wall cap')))
signal.alarm(cfg['wall_cap_seconds'])
begin=time.monotonic()
query=json.loads(Path(cfg['sources']['query_result']['path']).read_text())
assert query['status']=='SAT_MODEL_PENDING_AUDIT'
rows=Path(cfg['sources']['solver_stdout']['path']).read_text().splitlines()
assert any(line.strip()=='s SATISFIABLE' for line in rows)
assignment={}
for line in rows:
    if not line.startswith('v '):continue
    for term in line.split()[1:]:
        literal=int(term)
        if literal:assignment[abs(literal)]=int(literal>0)

R=PolynomialRing(GF(2),'u');u=R.gen();K=GF(2**41,name='u',modulus=u**41+u**3+1)
E=EllipticCurve(K,[1,0,0,0,1]);O=E(0);order=549756390943
dec=K.from_integer
enc=lambda v:sum(int(b)<<i for i,b in enumerate(v.polynomial().list()))
def bits(wires):return sum(assignment[w]<<i for i,w in enumerate(wires))
def halftrace(v):
    total=K.zero();t=v
    for _ in range(21):total+=t;t=t**4
    assert total*total+total==v
    return total
def source_points(a):
    h=halftrace(a);assert h
    return E.lift_x(K.one()+1/h,all=True)
def column(a):
    x=K.one()+1/halftrace(a)
    return min(enc(x**(1<<j)) for j in range(41))

target_line=Path(cfg['sources']['w10_input']['path']).read_text().splitlines()[1].split()
assert target_line[:2]==['T','0']
Q0=E(dec(int(target_line[2])),dec(int(target_line[3])))
Qk=E(Q0[0]**(1<<29),Q0[1]**(1<<29))
machine,wires,counts=circuit.build(enc(1/Qk[0]),cfg['sources']['w10_input']['path'])
assert len(assignment)==machine.next_var-1
values=[None]+[assignment[i] for i in range(1,machine.next_var)]
full_check=check_assignment(machine,values)
code_basis=[i for i in range(10) if i!=(56).bit_length()-1]
all_options=[];code_rows=[];all_columns=[]
for slot in range(4):
    code=bits(wires['mask'][slot]);assert 0<code<512
    a=sum((dec(1<<(i+1)) for j,i in enumerate(code_basis) if code>>j&1),K.zero())
    b=a+dec(112)
    assert a and b and a.trace()==0 and (1/a).trace()==0 and (1/b).trace()==0
    assert bits(wires['source_inverse'][slot])==enc(1/(a*b))
    col_a,col_b=column(a),column(b)
    all_columns += [col_a,col_b]
    za=dec(bits(wires['out'][slot]));assert za
    options=[]
    for ia,pa in enumerate(source_points(a)):
        for ib,pb in enumerate(source_points(b)):
            S=pa+pb
            if S!=O and S[0] and 1/S[0]==za:
                rot=[0,12,24,36][slot]
                options.append((E(S[0]**(1<<rot),S[1]**(1<<rot)),ia,ib))
    assert options
    all_options.append(options)
    code_rows.append({'slot':slot,'code':code,'source_masks':[enc(a),enc(b)],
                      'folded_columns':[col_a,col_b],'root_and_sign_options':len(options)})
assert len(set(all_columns))==8
found=None;checked_combinations=0
for choices in itertools.product(*all_options):
    checked_combinations+=1
    P=[entry[0] for entry in choices]
    M0=P[0]+P[1];M1=P[2]+P[3]
    if M0==O or M1==O or not M0[0] or not M1[0]:continue
    if enc(1/M0[0])!=bits(wires['middle'][0]) or enc(1/M1[0])!=bits(wires['middle'][1]):continue
    if M0+M1==Qk:
        found=choices;break
assert found is not None
transported=O
for item in found:
    P=item[0]
    transported+=E(P[0]**(1<<12),P[1]**(1<<12))
assert transported==Q0 and order*(4*transported)==O
signal.alarm(0)
result={'status':'PASS_INDEPENDENT_N41_W10_SAT_PUBLIC_RELATION','candidate_id':None,
        'curve_id':cfg['curve_id'],'orientation':29,'source_codes':[r['code'] for r in code_rows],
        'distinct_folded_columns':8,'raw_group_sum_matches_target':True,
        'back_transport_matches_public_target':True,'projected_subgroup_sum_matches_target':True,
        'model_clause_xor_check':full_check,'checked_sign_combinations':checked_combinations,
        'rows':code_rows,'wall_seconds':time.monotonic()-begin,
        'peak_rss_raw':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        'protocol_sha256':sha(HERE/'audit_protocol.json'),'script_sha256':sha(__file__)}
(HERE/'audit_result.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
print(json.dumps({'status':result['status'],'source_codes':result['source_codes'],
                  'checked_sign_combinations':checked_combinations},sort_keys=True))
