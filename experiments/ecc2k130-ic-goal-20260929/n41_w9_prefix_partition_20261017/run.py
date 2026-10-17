"""Sequential exact first-code prefix partition under one total N41 cap."""
import hashlib
import json
import os
import signal
import subprocess
import time
from pathlib import Path

import psutil

HERE=Path(__file__).resolve().parent
sha=lambda path:hashlib.sha256(Path(path).read_bytes()).hexdigest()
p=json.loads((HERE/'protocol.json').read_text())
for path,digest in p['sources'].items():assert sha(path)==digest,path
source=json.loads(Path(p['wires']).read_text())
allowed=source['allowed_code_words']
assert len(allowed)==71 and source['codes'][0][5:8]==p['prefix_wires']
counts={str(k):sum((code>>5)==k for code in allowed) for k in p['prefix_order']}
assert counts==p['source_counts'] and sum(counts.values())==71
base=Path(p['base_formula']).read_bytes()
header=b'p cnf 123218 339484\n'
assert base.startswith(header)
base_result=json.loads(Path(p['base_build_result']).read_text())
assert base_result['and_gates']==107285
assert base_result['formula_sha256']==sha(p['base_formula'])
temporary=HERE/'prefix_work.xcnf'
assert not temporary.exists() and not (HERE/'result.json').exists()
parent=psutil.Process(os.getpid())
started=time.monotonic();rows=[];global_status=None

for prefix in p['prefix_order']:
    if time.monotonic()-started>=p['total_wall_cap_seconds']:
        global_status='BOUNDED_UNKNOWN_TOTAL_CAP';break
    unit_lines=b''.join((f'{wire if (prefix>>bit)&1 else -wire} 0\n'.encode()
                         for bit,wire in enumerate(p['prefix_wires'])))
    formula=b'p cnf 123218 339487\n'+base[len(header):]+unit_lines
    temporary.write_bytes(formula)
    formula_hash=sha(temporary)
    output=HERE/f'prefix_{prefix}.stdout'
    errors=HERE/f'prefix_{prefix}.stderr'
    command=[p['solver'],'--threads=1',f"--maxtime={p['solver_cap_seconds']}",
             '--zero-exit-status','--verb=1','--printsol=1',str(temporary)]
    attempt_start=time.monotonic();peak=0;samples=0;monitor_error=None;stop=None
    with output.open('xb') as out,errors.open('xb') as err:
        child=subprocess.Popen(command,stdout=out,stderr=err,start_new_session=True)
        observed=psutil.Process(child.pid)
        while child.poll() is None:
            try:
                peak=max(peak,parent.memory_info().rss+observed.memory_info().rss)
                samples+=1
            except (psutil.NoSuchProcess,psutil.AccessDenied,PermissionError) as exc:
                if child.poll() is None:
                    monitor_error=type(exc).__name__;stop='MONITOR_FAILURE';break
            if peak>p['rss_cap_bytes']:stop='RSS_CAP';break
            if time.monotonic()-attempt_start>p['per_prefix_wall_cap_seconds']:
                stop='PREFIX_WALL_CAP';break
            if time.monotonic()-started>p['total_wall_cap_seconds']:
                stop='TOTAL_WALL_CAP';break
            time.sleep(.1)
        if stop and child.poll() is None:
            os.killpg(child.pid,signal.SIGTERM)
        exit_code=child.wait()
    text=output.read_text(errors='replace')
    if stop:
        status=stop
    elif 's SATISFIABLE' in text:
        status='SAT_MODEL_UNVERIFIED'
    elif 's UNSATISFIABLE' in text:
        status='UNSAT_UNVERIFIED'
    elif 's INDETERMINATE' in text:
        status='INDETERMINATE_SOLVER_CAP'
    else:
        status='PRODUCER_FAILURE_NO_TERMINAL_STATUS'
    restarts=[line for line in text.splitlines() if line.startswith('c rst')]
    row={'prefix':prefix,'source_code_count':counts[str(prefix)],
         'status':status,'command':command,'exit_code':exit_code,
         'formula_sha256':formula_hash,'stdout_sha256':sha(output),
         'stderr_sha256':sha(errors),'stop_reason':stop,
         'monitor_error':monitor_error,'rss_samples':samples,
         'sampled_peak_combined_rss_bytes':peak,
         'parent_wall_seconds':time.monotonic()-attempt_start,
         'last_restart_line':restarts[-1] if restarts else None}
    rows.append(row)
    temporary.unlink()
    (HERE/'partial.json').write_text(json.dumps({'status':'PARTIAL','rows':rows,
        'protocol_sha256':sha(HERE/'protocol.json')},sort_keys=True,indent=2)+'\n')
    print(json.dumps({k:row[k] for k in ('prefix','status','parent_wall_seconds',
                                          'sampled_peak_combined_rss_bytes')}),flush=True)
    if status=='SAT_MODEL_UNVERIFIED':
        global_status=status;break
    if status in ('RSS_CAP','MONITOR_FAILURE','TOTAL_WALL_CAP',
                  'PRODUCER_FAILURE_NO_TERMINAL_STATUS'):
        global_status=status;break

if global_status is None:
    if len(rows)==len(p['prefix_order']):
        global_status=('UNSAT_UNVERIFIED' if all(r['status']=='UNSAT_UNVERIFIED' for r in rows)
                       else 'BOUNDED_UNKNOWN')
    else:global_status='BOUNDED_UNKNOWN_TOTAL_CAP'
result={'status':global_status,'curve_id':p['curve_id'],'candidate_id':None,
        'worker_count':1,'prefix_order':p['prefix_order'],
        'source_counts':counts,'rows':rows,
        'panel_parent_wall_seconds':time.monotonic()-started,
        'target_dependent_base_build_seconds':base_result['total_seconds'],
        'charged_stage_wall_seconds':base_result['total_seconds']+time.monotonic()-started,
        'protocol_sha256':sha(HERE/'protocol.json')}
(HERE/'result.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
print(json.dumps({'status':global_status,'rows':len(rows),
                  'charged_stage_wall_seconds':result['charged_stage_wall_seconds']}),flush=True)
