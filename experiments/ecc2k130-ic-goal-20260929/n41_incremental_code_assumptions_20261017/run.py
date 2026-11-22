"""Monitor one incremental CryptoMiniSat process under frozen caps."""
import argparse
import hashlib
import json
import os
import psutil
import signal
import subprocess
import time
from pathlib import Path

D=Path(__file__).resolve().parent


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser=argparse.ArgumentParser();parser.add_argument('mode',choices=['pilot','full'])
    args=parser.parse_args();mode=args.mode
    p=json.loads((D/'protocol.json').read_text())
    r=json.loads((D/'run_protocol.json').read_text())
    assert r['protocol_sha256']==sha(D/'protocol.json')
    assert r['runner_sha256']==sha(Path(__file__))
    assert sha(D/'incremental')==p['binary_sha256']
    assert sha(Path(p['formula_path']))==p['formula_sha256']
    assert sha(D/'codes.tsv')==p['codes_sha256']
    assert sha(Path(p['lib_path']))==p['lib_sha256']
    command=[str(D/'incremental'),p['formula_path'],str(D/'codes.tsv'),
             str(1 if mode=='pilot' else 40),str(p['per_call_cpu_cap_s'])]
    out_path=D/(mode+'.stdout');err_path=D/(mode+'.stderr')
    parent=psutil.Process(os.getpid());start=time.monotonic()
    peak=0;stop=None;degraded=False
    with out_path.open('x') as out,err_path.open('x') as err:
        child=subprocess.Popen(command,stdout=out,stderr=err,start_new_session=True)
        process=psutil.Process(child.pid)
        while child.poll() is None:
            try:peak=max(peak,parent.memory_info().rss+process.memory_info().rss)
            except (psutil.NoSuchProcess,psutil.AccessDenied,PermissionError):
                if child.poll() is None:degraded=True
            if peak>p['rss_cap_bytes']:stop='RSS_CAP'
            elif time.monotonic()-start>p['parent_cap_s']:
                stop='PARENT_WALL_CAP'
            if stop:
                os.killpg(child.pid,signal.SIGTERM)
                break
            time.sleep(.05)
        child.wait()
    lines=out_path.read_text(errors='replace').splitlines()
    code_lines=[line for line in lines if line.startswith('CODE ')]
    model_lines=[line for line in lines if line.startswith('MODEL ')]
    status=('SAT_PENDING_REPLAY' if any(' SAT ' in x for x in code_lines)
            else 'PILOT_CENSORED' if mode=='pilot' and len(code_lines)==1 and child.returncode==0
            else 'ALL_CUBES_BOUNDED_OR_UNCERTIFIED' if mode=='full' and len(code_lines)==40 and child.returncode==0
            else 'BOUNDED_UNKNOWN' if stop else 'PRODUCER_FAILURE')
    result={'status':status,'mode':mode,'protocol_sha256':sha(D/'protocol.json'),
            'run_protocol_sha256':sha(D/'run_protocol.json'),
            'command':command,'exit_code':child.returncode,
            'stop_reason':stop,'wall_s':time.monotonic()-start,
            'sampled_peak_combined_rss_bytes':peak,'monitor_degraded':degraded,
            'load_lines':[x for x in lines if x.startswith('LOADED ')],
            'code_lines':code_lines,'model_line_count':len(model_lines),
            'stdout_sha256':sha(out_path),'stderr_sha256':sha(err_path)}
    (D/(mode+'_result.json')).write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
    print(json.dumps({k:result[k] for k in ('status','mode','wall_s',
        'sampled_peak_combined_rss_bytes','code_lines','load_lines')},sort_keys=True))


if __name__=='__main__':main()
