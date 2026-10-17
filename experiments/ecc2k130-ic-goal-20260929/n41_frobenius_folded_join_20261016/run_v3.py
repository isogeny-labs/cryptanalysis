import hashlib
import json
import pathlib
import re
import subprocess
import time
import resource

D=pathlib.Path(__file__).resolve().parent
BASE=D.parent/'n41_sixpair_shared_target_20261017'
INPUT=BASE/'join_input.tsv'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,o):p.write_text(json.dumps(o,indent=2,sort_keys=True)+'\n')
protocol={'input_sha256':sha(INPUT),'source_sha256':{'baseline':sha(BASE/'join_exact.cpp'),'folded':sha(D/'folded.cpp')},
          'binary_sha256':{a:sha(D/a) for a in ('baseline','folded')},'order':['baseline','folded','folded','baseline'],
          'cap_s_per_run':180,'rss_cap_bytes':4294967296,'rss_source':'resource.getrusage(RUSAGE_CHILDREN).ru_maxrss cumulative maximum',
          'target':[2026560328086,1928332930914],
          'prior_launch_failures':['/usr/bin/time -l returned 1 after child because sysctl kern.clockrate was denied','ps sampling was denied by sandbox']}
write(D/'protocol_v3.json',protocol)
records=[]
for i,arm in enumerate(protocol['order']):
    out=D/f'v3_run_{i}_{arm}.stdout';err=D/f'v3_run_{i}_{arm}.stderr'
    t=time.monotonic()
    with out.open('w') as fo,err.open('w') as fe:
        p=subprocess.run([str(D/arm),str(INPUT)],stdout=fo,stderr=fe,timeout=180)
    code=p.returncode
    wall=time.monotonic()-t
    peak=resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss
    hit=re.search(r'^HIT (.+)$',out.read_text(),re.M)
    rec={'arm':arm,'exit_code':code,'parent_wall_s':wall,'worker_hit_line':hit.group(0) if hit else None,
         'cumulative_child_peak_rss_bytes':peak,'stdout_sha256':sha(out),'stderr_sha256':sha(err)}
    records.append(rec);write(D/'result_v3.json',{'protocol_sha256':sha(D/'protocol_v3.json'),'runs':records})
    print(json.dumps(rec),flush=True)
assert all(r['exit_code']==0 and r['worker_hit_line'] and r['cumulative_child_peak_rss_bytes']<4294967296 for r in records)
assert len({tuple(r['worker_hit_line'].split()[1:9]) for r in records})==1
print('PASS exact witness and probe counts',flush=True)
