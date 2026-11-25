"""Independent native all-pair replay of the 4,096-code NTL panel."""
import hashlib
import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

import psutil

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
PRIOR = ROOT / 'n131_w20_global_norm_pilot_20261018'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    cfg_path = HERE / 'direct_protocol_4096.json'
    cfg = json.loads(cfg_path.read_text())
    files = {
        'direct_run.py': HERE / 'direct_run.py',
        'direct_audit.cpp': PRIOR / 'direct_audit.cpp',
        'direct_audit': PRIOR / 'direct_audit',
        'field.hpp': ROOT / 'n131_w20_paired_raw_quotient_20261016/field.hpp',
        'support_w20.tsv': ROOT / 'n131_w20_sevenpair_gate_20261010/support_w20.tsv',
        'coefficients.tsv': PRIOR / 'coefficients.tsv',
        'sage_runtime_info.json': HERE / 'sage_runtime_info.json',
    }
    assert cfg['source_sha256'] == {name: sha(path) for name,path in files.items()}
    command = [str(files['direct_audit']),str(files['support_w20.tsv']),
               str(files['coefficients.tsv']),'4096']
    assert cfg['command'] == command and cfg['worker_count'] == 1
    started = time.monotonic_ns()
    peak = 0
    stop = None
    degraded = False
    misses = 0
    with (HERE / 'direct_stdout_4096.txt').open('x') as out, (HERE / 'direct_stderr_4096.txt').open('x') as err:
        child = subprocess.Popen(command,stdout=out,stderr=err,start_new_session=True)
        proc = psutil.Process(child.pid)
        parent = psutil.Process()
        while child.poll() is None:
            try:
                peak = max(peak,proc.memory_info().rss+parent.memory_info().rss)
                misses = 0
            except (psutil.NoSuchProcess,psutil.AccessDenied,PermissionError):
                if child.poll() is None:
                    misses += 1
                    degraded = degraded or misses>=2
            if peak>cfg['rss_cap_bytes']:
                stop='RSS_CAP'
            elif time.monotonic_ns()-started>cfg['wall_cap_seconds']*10**9:
                stop='WALL_CAP'
            if stop:
                os.killpg(child.pid,signal.SIGTERM)
                break
            time.sleep(0.05)
        child.wait()
    ended = time.monotonic_ns()
    lines = (HERE/'direct_stdout_4096.txt').read_text(errors='replace').splitlines()
    status = ('BOUNDED_UNKNOWN' if stop else
              'COMPLETE_INDEPENDENT_DIRECT_4096' if child.returncode==0 and
              not (HERE/'direct_stderr_4096.txt').read_bytes() and len(lines)==2
              else 'PRODUCER_FAILURE')
    receipt = {'status':status,'candidate_id':None,'exit_code':child.returncode,
               'stop_reason':stop,'monitor_degraded':degraded,'wall_ns':ended-started,
               'sampled_peak_combined_rss_bytes':peak,'lines':lines,
               'protocol_sha256':sha(cfg_path),
               'stdout_sha256':sha(HERE/'direct_stdout_4096.txt'),
               'stderr_sha256':sha(HERE/'direct_stderr_4096.txt')}
    (HERE/'direct_receipt_4096.json').write_text(json.dumps(receipt,sort_keys=True,indent=2)+'\n')
    print(json.dumps(receipt,sort_keys=True),flush=True)
    return 0 if status=='COMPLETE_INDEPENDENT_DIRECT_4096' else 1


if __name__=='__main__':
    sys.exit(main())
