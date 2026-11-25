#!/usr/bin/env python3
"""Local independent-formula recount, exact replay and mutation controls.
Not an independent signed proof-carrying-verification verdict.
"""
import copy, hashlib, json, math, subprocess, sys, tempfile
from pathlib import Path
DIR=Path(__file__).resolve().parent
SRC=DIR/'replay.py'
SUMMARY=DIR/'RESULTS_SUMMARY.json'
p=1009

def count_points(a,b):
 n=1
 for x in range(p):
  v=(x*x*x+a*x+b)%p
  n+=1 if v==0 else (2 if pow(v,(p-1)//2,p)==1 else 0)
 return n

def replay_matches(path):
 cp=subprocess.run([sys.executable,str(SRC),'--verify-json',str(path)],
                   capture_output=True,text=True)
 return cp.returncode==0

def validate(data,expected):
 params=data['parameters'];cnt=data['counts'];cost=data['costs']['totals']
 assert (params['p'],params['a'],params['b'],params['nonsquare'])==(1009,2,25,11)
 assert params['twist_a']==242 and params['twist_b']==987
 assert count_points(2,25)==params['source_order']==expected['source_order']
 assert count_points(242,987)==params['twist_order']==expected['twist_order']
 assert params['extension_order']==(p+1)**2-(p+1-991)**2==expected['extension_order']
 assert params['twist_order_factors']=={'3':1,'7':3}
 assert cnt['distinct_images']==991 and cnt['intersection_twist_rational']==1
 assert cnt['trace_rational_inverse_checks']==1029
 assert cnt['dlps']==len(data['samples'])==expected['dlp_sample_count']==64
 assert [x['k'] for x in data['samples'][:3]]==[0,1,990]
 assert len({x['k'] for x in data['samples']})==64
 for field in ('direct','lifted'):
  for op in ('group_calls','add','mul','inv'):
   assert cost[field][op]==sum(row[field][op] for row in data['samples'])
   expected_field='direct_solver' if field=='direct' else 'extension_solver'
   assert cost[field][op]==expected[expected_field][op]
 assert cnt['homomorphism_pairs']==expected['homomorphism_pairs_checked']
 assert data['obligations']['independent_signed_pcc']=='PENDING'

def main():
 expected=json.loads(SUMMARY.read_text())
 with tempfile.TemporaryDirectory() as td:
  path=Path(td)/'raw.json'
  cp=subprocess.run([sys.executable,str(SRC),'--out',str(path)],
                    check=True,capture_output=True,text=True)
  result=json.loads(path.read_text())
  validate(result,expected)
  digest=hashlib.sha256(path.read_bytes()).hexdigest()
  assert digest==expected['local_full_results_sha256'],(digest,expected['local_full_results_sha256'])
  assert replay_matches(path)
  for name,mutation in (
    ('wrong-twist-order',lambda x:x['parameters'].__setitem__('twist_order',1028)),
    ('forged-group-cost',lambda x:x['samples'][0]['direct'].__setitem__('mul',1)),
    ('altered-scalar',lambda x:x['samples'][0].__setitem__('k',123))
  ):
   corrupted=copy.deepcopy(result)
   mutation(corrupted)
   f=Path(td)/(name+'.json')
   f.write_text(json.dumps(corrupted,sort_keys=True,indent=2)+'\n')
   assert not replay_matches(f),name
   try:validate(corrupted,expected)
   except AssertionError:pass
   else:raise AssertionError('validator accepted '+name)
 print('PASS local Legendre recount, 64-case exact output, three mutation rejects')
 print('raw_sha256',digest)
if __name__=='__main__':main()
