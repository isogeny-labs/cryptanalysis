"""Run the frozen native CLI cells using the lab's existing process watchdog."""
import hashlib
import importlib.util
import json
import os
import platform
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[4]
WORKSPACE = REPO.parent.parent
spec = importlib.util.spec_from_file_location('lead_sweep', WORKSPACE/'tools/lead_sweep.py')
watch = importlib.util.module_from_spec(spec)
spec.loader.exec_module(watch)

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def main():
    raw = HERE/'raw'
    raw.mkdir(exist_ok=False)
    binary = REPO/'suite/target/debug/ca-ic'
    manifest = {
        'scope': 'CPU-only debug-build local feasibility; producer assertions, pcc:unverified',
        'authorization': 'User explicitly authorized local runs; S3 admission waived for this task.',
        'commit': subprocess.check_output(['git','rev-parse','HEAD'],cwd=REPO,text=True).strip(),
        'patch_sha256': hashlib.sha256(subprocess.check_output(['git','diff','HEAD'],cwd=REPO)).hexdigest(),
        'binary_sha256': sha(binary), 'cargo_lock_sha256': sha(REPO/'suite/Cargo.lock'),
        'protocol_sha256': sha(HERE/'PROTOCOL.md'),
        'platform': platform.platform(), 'cpu': Path('/proc/cpuinfo').read_text().split('model name')[1].splitlines()[0],
        'cpu_count': os.cpu_count(), 'memory': Path('/proc/meminfo').read_text(),
        'cells': [],
    }
    for n,d in [(7,3),(13,3),(17,4)]:
        for seed in (1,2):
            arms=[('chain-m31-serial','chain-sat:m=31,topology=serial,conflicts=1000,models=4,branching=coordinates',4),
                  ('chain-m31-balanced','chain-sat:m=31,topology=balanced,conflicts=1000,models=4,branching=coordinates',4)]
            for name,oracle,trials in arms:
                label=f'n{n}-seed{seed}-{name}'
                output=raw/(label+'.json')
                command=[str(binary),'--json','--out',str(output),'bench',
                         '--char2-degree',str(n),'--factor-base',f'binary-subspace:dimension={d}',
                         '--oracle',oracle,'--targets','walk','--max-trials',str(trials),
                         '--seed',str(seed),'--repeats','1','--rho-runs','1','--threads','1',
                         '--solver-budget-seconds','10','--max-cofactor','8']
                status=watch.watched_run(command,raw/(label+'.txt'),2,20,cwd=REPO)
                row={'label':label,'degree':n,'dimension':d,'seed':seed,'arm':name,'command':command,**status}
                if output.exists():
                    report=json.loads(output.read_text())
                    row['native_status']=report.get('status')
                    row['native_rows']=report.get('rows',[])
                    row['native_error']=report.get('message')
                    if report.get('status') == 'incomplete' and status.get('exit_code') == 1:
                        row['watch_status']=row['status']
                        row['status']='native_incomplete'
                    row['report_sha256']=sha(output)
                manifest['cells'].append(row)
                (HERE/'manifest.json').write_text(json.dumps(manifest,indent=2))
                print(json.dumps({k:v for k,v in row.items() if k not in ('native_rows','command')}),flush=True)

if __name__=='__main__': main()
