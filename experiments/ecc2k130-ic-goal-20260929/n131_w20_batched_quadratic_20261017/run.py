"""Parent-capped ABBA comparison on frozen N131 queries."""
import hashlib
import json
import resource
import subprocess
import time
from pathlib import Path

D=Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


protocol=json.loads((D/'protocol.json').read_text())
assert protocol['runner_sha256']==sha(Path(__file__))
for item in protocol['sources'].values():
    assert sha(Path(item['path']))==item['sha256']
result=[]
for implementation,mode in protocol['order']:
    binary=Path(protocol['sources'][('batch_binary' if implementation=='batch' else 'baseline_binary')]['path'])
    output=D/f'{implementation}_{mode}.json'
    out=D/f'{implementation}_{mode}.stdout'
    err=D/f'{implementation}_{mode}.stderr'
    command=[str(binary),mode,
             protocol['sources']['fixture']['path'],
             protocol['sources']['support']['path'],
             protocol['sources']['valid']['path'],str(output),
             str(protocol['cap_s_per_query']),str(protocol['rss_cap_bytes'])]
    started=time.monotonic()
    with out.open('x') as out_stream,err.open('x') as err_stream:
        try:
            process=subprocess.run(command,stdout=out_stream,stderr=err_stream,
                                   timeout=protocol['cap_s_per_query'])
            code,timed_out=process.returncode,False
        except subprocess.TimeoutExpired:
            code,timed_out=None,True
    wall=time.monotonic()-started
    row={'implementation':implementation,'mode':mode,'command':command,
         'exit_code':code,'timed_out':timed_out,'parent_wall_s':wall,
         'child_ru_maxrss_raw':resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss,
         'stdout_sha256':sha(out),'stderr_sha256':sha(err),
         'result_sha256':sha(output) if output.exists() else None,
         'result_status':json.loads(output.read_text())['status'] if output.exists() else None}
    result.append(row)
    print(json.dumps({key:row[key] for key in ('implementation','mode','exit_code',
                                               'timed_out','parent_wall_s','result_status')}),flush=True)
    (D/'run_result.json').write_text(json.dumps({'status':'PARTIAL' if len(result)<len(protocol['order']) else 'COMPLETE',
                                                'protocol_sha256':sha(D/'protocol.json'),
                                                'rows':result},sort_keys=True,indent=2)+'\n')
