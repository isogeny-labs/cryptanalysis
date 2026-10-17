"""Enumerate all allowed first-slot source-code cubes with capped SAT."""
import argparse
import hashlib
import json
import os
import signal
import subprocess
import time
from pathlib import Path
import psutil

D=Path(__file__).resolve().parent


def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(1<<20),b''):h.update(block)
    return h.hexdigest()


def read(path):return json.loads(path.read_text())


def run_cube(code,wires,base,protocol):
    stem=f'cube_{code:03d}'
    path=D/(stem+'.xcnf')
    first,tail=base.split(b'\n',1)
    tag,kind,var_count,clause_count=first.decode().split()
    assert (tag,kind)==('p','cnf') and len(wires)==7
    units=''.join(f"{wire if code>>j&1 else -wire} 0\n"
                  for j,wire in enumerate(wires)).encode()
    path.write_bytes(f'p cnf {var_count} {int(clause_count)+7}\n'.encode()+tail+units)
    command=[protocol['solver_path'],*protocol['flags'],str(path)]
    start=time.monotonic();peak=0;stop=None;degraded=False
    parent=psutil.Process(os.getpid())
    out_path=D/(stem+'.stdout');err_path=D/(stem+'.stderr')
    with out_path.open('x') as out,err_path.open('x') as err:
        child=subprocess.Popen(command,stdout=out,stderr=err,start_new_session=True)
        process=psutil.Process(child.pid)
        while child.poll() is None:
            try:peak=max(peak,parent.memory_info().rss+process.memory_info().rss)
            except (psutil.NoSuchProcess,psutil.AccessDenied,PermissionError):
                if child.poll() is None:degraded=True
            if peak>protocol['rss_cap_bytes']:stop='RSS_CAP'
            elif time.monotonic()-start>protocol['one_cube_parent_cap_s']:
                stop='PARENT_WALL_CAP'
            if stop:
                os.killpg(child.pid,signal.SIGTERM)
                break
            time.sleep(.05)
        child.wait()
    stdout=out_path.read_text(errors='replace')
    terminal=[x.strip() for x in stdout.splitlines() if x.startswith('s ')]
    status=('SAT_PENDING_REPLAY' if 's SATISFIABLE' in terminal
            else 'UNSAT_UNCERTIFIED' if 's UNSATISFIABLE' in terminal
            else 'BOUNDED_UNKNOWN' if stop or any('INDETERMINATE' in x for x in terminal)
            else 'PRODUCER_FAILURE')
    result={'status':status,'code':code,'protocol_sha256':sha(D/'protocol.json'),
            'run_protocol_sha256':sha(D/'run_protocol.json'),
            'input_sha256':sha(path),'command':command,
            'exit_code':child.returncode,'stop_reason':stop,
            'wall_s':time.monotonic()-start,'sampled_peak_combined_rss_bytes':peak,
            'monitor_degraded':degraded,'terminal_lines':terminal,
            'restart_lines':sum(x.startswith('c rst ') for x in stdout.splitlines()),
            'stdout_sha256':sha(out_path),'stderr_sha256':sha(err_path)}
    (D/(stem+'_result.json')).write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
    print(json.dumps({k:result[k] for k in ('code','status','wall_s','restart_lines',
                                             'sampled_peak_combined_rss_bytes')},sort_keys=True),flush=True)
    return result


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--max-new',type=int,default=40)
    parser.add_argument('--summary',required=True)
    args=parser.parse_args()
    protocol=read(D/'protocol.json');run_protocol=read(D/'run_protocol.json')
    assert run_protocol['protocol_sha256']==sha(D/'protocol.json')
    assert run_protocol['runner_sha256']==sha(Path(__file__))
    assert sha(D/'rebuilt_public.xcnf')==protocol['rebuilt_formula_sha256']
    assert sha(Path(protocol['solver_path']))==protocol['solver_sha256']
    mapping=read(D/'wires.json')
    assert sha(D/'wires.json')==protocol['wires_sha256']
    assert mapping['allowed_codes']==protocol['allowed_codes']
    base=(D/'rebuilt_public.xcnf').read_bytes()
    results=[];new=0
    for code in protocol['allowed_codes']:
        result_path=D/f'cube_{code:03d}_result.json'
        if result_path.exists():
            result=read(result_path)
        else:
            if new>=args.max_new:break
            if sum(item['wall_s'] for item in results)>=protocol['overall_parent_cap_s']:
                break
            result=run_cube(code,mapping['code_wires'],base,protocol)
            new+=1
        results.append(result)
        if result['status']=='SAT_PENDING_REPLAY' or result['status']=='PRODUCER_FAILURE':break
    status=('SAT_PENDING_REPLAY' if any(x['status']=='SAT_PENDING_REPLAY' for x in results)
            else 'PRODUCER_FAILURE' if any(x['status']=='PRODUCER_FAILURE' for x in results)
            else 'ALL_CUBES_BOUNDED_OR_UNCERTIFIED' if len(results)==len(protocol['allowed_codes'])
            else 'PARTIAL')
    summary={'status':status,'protocol_sha256':sha(D/'protocol.json'),
             'run_protocol_sha256':sha(D/'run_protocol.json'),
             'completed_codes':[x['code'] for x in results],
             'result_sha256':{str(x['code']):sha(D/f"cube_{x['code']:03d}_result.json")
                              for x in results},
             'sum_cube_wall_s':sum(x['wall_s'] for x in results),
             'new_cubes_this_invocation':new}
    (D/args.summary).write_text(json.dumps(summary,sort_keys=True,indent=2)+'\n')
    print(json.dumps(summary,sort_keys=True),flush=True)


if __name__=='__main__':main()
