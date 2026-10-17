import hashlib
import json
import pathlib
import re
import subprocess
import time

D=pathlib.Path(__file__).resolve().parent
BASE=D.parent/'n41_sixpair_shared_target_20261017'
INPUT=BASE/'join_input.tsv'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,o):p.write_text(json.dumps(o,indent=2,sort_keys=True)+'\n')
protocol={'input_sha256':sha(INPUT),'source_sha256':{'baseline':sha(BASE/'join_exact.cpp'),'folded':sha(D/'folded.cpp')},
          'binary_sha256':{a:sha(D/a) for a in ('baseline','folded')},'order':['baseline','folded','folded','baseline'],
          'cap_s_per_run':180,'rss_cap_bytes':4294967296,'rss_poll_s':0.05,
          'target':[2026560328086,1928332930914],
          'prior_launch_failure':'/usr/bin/time -l returned 1 after child because sysctl kern.clockrate was denied'}
write(D/'protocol_v2.json',protocol)
records=[]
for i,arm in enumerate(protocol['order']):
    out=D/f'v2_run_{i}_{arm}.stdout';err=D/f'v2_run_{i}_{arm}.stderr'
    t=time.monotonic();peak=0
    with out.open('w') as fo,err.open('w') as fe:
        p=subprocess.Popen([str(D/arm),str(INPUT)],stdout=fo,stderr=fe)
        while p.poll() is None:
            q=subprocess.run(['ps','-o','rss=','-p',str(p.pid)],capture_output=True,text=True)
            if q.returncode==0 and q.stdout.strip():peak=max(peak,int(q.stdout.strip())*1024)
            if peak>protocol['rss_cap_bytes'] or time.monotonic()-t>180:
                p.kill();break
            time.sleep(0.05)
        code=p.wait()
    wall=time.monotonic()-t
    hit=re.search(r'^HIT (.+)$',out.read_text(),re.M)
    rec={'arm':arm,'exit_code':code,'parent_wall_s':wall,'worker_hit_line':hit.group(0) if hit else None,
         'sampled_peak_rss_bytes':peak,'stdout_sha256':sha(out),'stderr_sha256':sha(err)}
    records.append(rec);write(D/'result_v2.json',{'protocol_sha256':sha(D/'protocol_v2.json'),'runs':records})
    print(json.dumps(rec),flush=True)
assert all(r['exit_code']==0 and r['worker_hit_line'] and r['sampled_peak_rss_bytes']<4294967296 for r in records)
assert len({tuple(r['worker_hit_line'].split()[1:9]) for r in records})==1
print('PASS exact witness and probe counts',flush=True)
