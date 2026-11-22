"""Freeze four distinct N41 W11 pair rotations from the audited five-pair table."""
import hashlib,json,sys
from pathlib import Path
H=Path(__file__).resolve().parent
ROOT=Path('/Volumes/SSD990/cryptanalysis/experiments/ecc2k130-ic-goal-20260929/output_first_fifth_20261019')
sys.path.insert(0,str(ROOT))
from output_first_math import FixedSeed
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
cfg=json.loads((H/'prepare_protocol.json').read_text())
assert cfg['status']=='FROZEN_BEFORE_N41_FOURPAIR_PREPARE'
for k,v in cfg['sources'].items():assert sha(v['path'])==v['sha256'],k
fixed=FixedSeed(41,[0,3],56,11)
source=Path(cfg['sources']['fivepair_table']['path']).read_text().splitlines()
assert source[0]=='W11FIVE 5 1124 1'
states={};checks=[];target=None
for line in source[1:]:
 p=line.split()
 if p[0]=='T':target=tuple(map(int,p[2:]))
 elif p[0]=='S':
  slot,sid,code,branch,a,b,ca,cb,x,y=map(int,p[1:]);states[(slot,sid)]=[code,branch,a,b,ca,cb,x,y]
 elif p[0]=='C':checks.append(line)
assert len(states)==5620 and len(checks)==128 and fixed.e.on_curve(target)
lines=['W11FOUR 4 1124 1',f'T 0 {target[0]} {target[1]}']
for new,old,rot in [(0,0,0),(1,2,12),(2,4,24),(3,0,36)]:
 for sid in range(1124):
  code,branch,a,b,ca,cb,x,y=states[(old,sid)]
  if new==3:x,y=fixed.e.frob((x,y),36)
  assert fixed.e.on_curve((x,y))
  lines.append('S '+ ' '.join(map(str,[new,sid,code,branch,a,b,ca,cb,x,y])))
lines.extend(checks)
out=H/'join4_input.tsv';out.write_text('\n'.join(lines)+'\n')
res={'status':'COMPLETE_N41_FOURPAIR_PREPARE','candidate_id':None,'curve_id':cfg['curve_id'],
 'rotations':[0,12,24,36],'states_per_slot':1124,'target_point':list(target),
 'addition_checks':128,'input_sha256':sha(out),'protocol_sha256':sha(H/'prepare_protocol.json'),
 'script_sha256':sha(Path(__file__))}
(H/'prepare_result.json').write_text(json.dumps(res,sort_keys=True,indent=2)+'\n')
print(json.dumps(res,sort_keys=True))
