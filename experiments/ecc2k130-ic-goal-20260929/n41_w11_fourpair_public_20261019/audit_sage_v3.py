"""Independently rebuild eight N41 source points and four-pair public relation."""
import hashlib,json,resource,signal,time
from pathlib import Path
from sage.all import EllipticCurve,GF,PolynomialRing
H=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
cfg=json.loads((H/'audit_v3_protocol.json').read_text())
assert cfg['status']=='FROZEN_BEFORE_N41_FOURPAIR_SAGE_AUDIT_V3'
for k,v in cfg['sources'].items():assert sha(v['path'])==v['sha256'],k
signal.signal(signal.SIGALRM,lambda *_:(_ for _ in ()).throw(TimeoutError('audit wall cap')))
signal.alarm(cfg['wall_cap_seconds'])
start=time.monotonic()
query=json.loads(Path(cfg['sources']['query_result']['path']).read_text())
assert query['status']=='COMPLETE_HIT'
hit=query['terminal_line'].split();assert hit[0]=='HIT'
orientation=int(hit[1]);ids=list(map(int,hit[2:6]))
assert orientation==3 and len(ids)==4
R=PolynomialRing(GF(2),'u');u=R.gen();K=GF(2**41,name='u',modulus=u**41+u**3+1)
E=EllipticCurve(K,[1,0,0,0,1]);O=E(0);order=549756390943
dec=K.from_integer
enc=lambda v:sum(int(b)<<i for i,b in enumerate(v.polynomial().list()))
def halftrace(v):
 out=K.zero();t=v
 for _ in range(21):out+=t;t=t**4
 assert out*out+out==v
 return out
def source_points(a):
 h=halftrace(a);assert h
 x=K.one()+1/h
 return E.lift_x(x,all=True)
def column(a):
 x=K.one()+1/halftrace(a)
 return min(enc(x**(1<<j)) for j in range(41))
lines=Path(cfg['sources']['join_input']['path']).read_text().splitlines()
assert lines[0]=='W11FOUR 4 1124 1'
Q0=None;selected={}
for line in lines[1:]:
 c=line.split()
 if c[0]=='T':Q0=E(dec(int(c[2])),dec(int(c[3])))
 elif c[0]=='S':
  slot,sid=map(int,c[1:3])
  if sid==ids[slot]:selected[slot]=list(map(int,c[3:]))
assert Q0 is not None and len(selected)==4
Qk=E(Q0[0]**(1<<orientation),Q0[1]**(1<<orientation))
assert [enc(Qk[0]),enc(Qk[1])]==list(map(int,hit[9:11]))
rotations=[0,12,24,36]
raw=O;transported=O;cols=[];rows=[]
for slot in range(4):
 code,branch,ma,mb,ca,cb,x,y=selected[slot]
 bits=[0,1,2,3,4,6,7,8,9,10]
 a=sum((dec(1<<(bit+1)) for j,bit in enumerate(bits) if code>>j&1),K.zero())
 b=a+dec(112)
 assert enc(a)==ma and enc(b)==mb
 assert a and b and a.trace()==0 and (1/a).trace()==0 and (1/b).trace()==0
 assert column(a)==ca and column(b)==cb
 pa,pb=source_points(a),source_points(b)
 observed=E(dec(x),dec(y));options=[]
 for ia,aa in enumerate(pa):
  for ib,bb in enumerate(pb):
   S=aa+bb
   rotated=E(S[0]**(1<<rotations[slot]),S[1]**(1<<rotations[slot]))
   if rotated==observed:options.append((ia,ib,aa,bb))
 assert len(options)==1 and branch==2*options[0][0]+options[0][1]
 assert observed!=O and observed[0]
 assert order*(4*options[0][2])==O and order*(4*options[0][3])==O
 raw+=observed
 back=E(observed[0]**(1<<(41-orientation)),observed[1]**(1<<(41-orientation)))
 transported+=back
 cols.extend([ca,cb])
 rows.append({'slot':slot,'state_id':ids[slot],'source_code':code,
              'source_masks':[ma,mb],'source_signs':[options[0][0],options[0][1]],
              'folded_columns':[ca,cb],'pair_point':[x,y],
              'rotation':rotations[slot],'back_transported_point':[enc(back[0]),enc(back[1])]})
assert len(set(cols))==8
assert raw==Qk and transported==Q0
assert 4*raw!=O and order*(4*raw)==O
assert 4*transported!=O and order*(4*transported)==O
signal.alarm(0)
res={'status':'PASS_INDEPENDENT_N41_W11_FOURPAIR_PUBLIC_RELATION','candidate_id':None,
 'curve_id':cfg['curve_id'],'raw_target_point':[enc(Q0[0]),enc(Q0[1])],
 'oriented_target_point':[enc(Qk[0]),enc(Qk[1])],'orientation':orientation,
 'source_codes':[r['source_code'] for r in rows],
 'distinct_folded_columns':8,'summand_count':8,
 'raw_group_sum_matches_target':True,'back_transport_matches_public_target':True,
 'projected_subgroup_sum_matches_target':True,'subgroup_order':order,'cofactor':4,
 'rows':rows,'wall_seconds':time.monotonic()-start,
 'peak_rss_raw':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
 'protocol_sha256':sha(H/'audit_v3_protocol.json'),'script_sha256':sha(Path(__file__))}
(H/'audit_result.json').write_text(json.dumps(res,sort_keys=True,indent=2)+'\n')
print(json.dumps({k:res[k] for k in ('status','orientation','source_codes','distinct_folded_columns','wall_seconds')},sort_keys=True))
