"""Alternating same-point CPU comparison with the archived batched oracle."""
import hashlib
import json
import resource
import subprocess
import time
from pathlib import Path

HERE=Path(__file__).resolve().parent
sha=lambda path:hashlib.sha256(Path(path).read_bytes()).hexdigest()
p=json.loads((HERE/'benchmark_protocol.json').read_text())
for path,digest in p['sources'].items():assert sha(path)==digest,path
rows=[]
for index,(arm,mode) in enumerate(p['order']):
    binary=p['binaries'][arm]
    result=HERE/f'paired_{index:02}_{arm}_{mode}.json'
    stdout=HERE/f'paired_{index:02}_{arm}_{mode}.stdout'
    stderr=HERE/f'paired_{index:02}_{arm}_{mode}.stderr'
    command=[binary,mode,p['fixture'],p['support'],p['valid_bitmap'],
             str(result),str(p['cap_seconds']),str(p['rss_cap_bytes'])]
    before=resource.getrusage(resource.RUSAGE_CHILDREN)
    start=time.monotonic()
    with stdout.open('x') as out,stderr.open('x') as err:
        try:
            child=subprocess.run(command,stdout=out,stderr=err,
                                 timeout=p['cap_seconds'])
            exit_code,timed_out=child.returncode,False
        except subprocess.TimeoutExpired:
            exit_code,timed_out=None,True
    wall=time.monotonic()-start
    after=resource.getrusage(resource.RUSAGE_CHILDREN)
    try:data=json.loads(result.read_text())
    except (FileNotFoundError,json.JSONDecodeError):data=None
    row={'arm':arm,'mode':mode,'command':command,'exit_code':exit_code,
         'timed_out':timed_out,'parent_wall_s':wall,
         'child_cpu_s':after.ru_utime-before.ru_utime+after.ru_stime-before.ru_stime,
         'child_user_cpu_s':after.ru_utime-before.ru_utime,
         'child_system_cpu_s':after.ru_stime-before.ru_stime,
         'result_sha256':sha(result) if data else None,
         'stdout_sha256':sha(stdout),'stderr_sha256':sha(stderr),
         'result_status':data['status'] if data else None,
         'setup_ns':data.get('setup_ns') if data else None,
         'query_ns':data.get('query_ns') if data else None,
         'native_peak_rss_bytes':data.get('peak_rss_bytes') if data else None}
    rows.append(row)
    (HERE/'paired_cpu_result.json').write_text(json.dumps({
         'status':'PARTIAL' if len(rows)<len(p['order']) else 'COMPLETE',
         'protocol_sha256':sha(HERE/'benchmark_protocol.json'),
         'rows':rows},sort_keys=True,indent=2)+'\n')
    print(json.dumps({k:row[k] for k in ('arm','mode','exit_code',
          'parent_wall_s','child_cpu_s')}),flush=True)
