"""Reverse-order paired queries with per-child CPU resource deltas."""
import hashlib
import json
import resource
import subprocess
import time
from pathlib import Path

D=Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


base=json.loads((D/'protocol.json').read_text())
protocol=json.loads((D/'cpu_protocol.json').read_text())
assert protocol['prior_protocol_sha256']==sha(D/'protocol.json')
assert protocol['prior_result_sha256']==sha(D/'run_result.json')
assert protocol['runner_sha256']==sha(Path(__file__))
for item in base['sources'].values():assert sha(Path(item['path']))==item['sha256']
rows=[]
for implementation,mode in protocol['order']:
    binary=Path(base['sources']['batch_binary' if implementation=='batch' else 'baseline_binary']['path'])
    result=D/f'cpu_{implementation}_{mode}.json'
    stdout=D/f'cpu_{implementation}_{mode}.stdout'
    stderr=D/f'cpu_{implementation}_{mode}.stderr'
    command=[str(binary),mode,base['sources']['fixture']['path'],
             base['sources']['support']['path'],base['sources']['valid']['path'],
             str(result),str(protocol['cap_s_per_query']),str(protocol['rss_cap_bytes'])]
    before=resource.getrusage(resource.RUSAGE_CHILDREN)
    start=time.monotonic()
    with stdout.open('x') as out,stderr.open('x') as err:
        try:
            proc=subprocess.run(command,stdout=out,stderr=err,
                                timeout=protocol['cap_s_per_query'])
            code,timed_out=proc.returncode,False
        except subprocess.TimeoutExpired:
            code,timed_out=None,True
    wall=time.monotonic()-start
    after=resource.getrusage(resource.RUSAGE_CHILDREN)
    row={'implementation':implementation,'mode':mode,'command':command,
         'exit_code':code,'timed_out':timed_out,'parent_wall_s':wall,
         'child_user_cpu_s':after.ru_utime-before.ru_utime,
         'child_system_cpu_s':after.ru_stime-before.ru_stime,
         'child_ru_maxrss_raw':after.ru_maxrss,
         'stdout_sha256':sha(stdout),'stderr_sha256':sha(stderr),
         'result_sha256':sha(result) if result.exists() else None,
         'result_status':json.loads(result.read_text())['status'] if result.exists() else None}
    rows.append(row)
    print(json.dumps({k:row[k] for k in ('implementation','mode','exit_code',
                   'parent_wall_s','child_user_cpu_s','child_system_cpu_s')}),flush=True)
    (D/'cpu_result.json').write_text(json.dumps({'status':'PARTIAL' if len(rows)<4 else 'COMPLETE',
           'protocol_sha256':sha(D/'cpu_protocol.json'),'rows':rows},sort_keys=True,indent=2)+'\n')
