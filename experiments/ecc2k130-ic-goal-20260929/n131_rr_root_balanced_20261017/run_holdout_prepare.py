"""Launch the checked local Sage selector with a parent cap."""
import hashlib
import json
import resource
import subprocess
import time
from pathlib import Path

D=Path(__file__).resolve().parent
LAUNCHER=Path('/Volumes/SSD990/cryptanalysis/sage')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


protocol=json.loads((D/'holdout_prepare_protocol.json').read_text())
assert protocol['producer_sha256']==sha(D/'prepare_holdout_sage.py')
assert (D/'sage_runtime_info.json').exists()
command=[str(LAUNCHER),'-python',str(D/'prepare_holdout_sage.py')]
start=time.monotonic()
try:
    proc=subprocess.run(command,capture_output=True,timeout=protocol['wall_cap_s'])
    out,err,code,timed_out=proc.stdout,proc.stderr,proc.returncode,False
except subprocess.TimeoutExpired as exc:
    out,err,code,timed_out=exc.stdout or b'',exc.stderr or b'',None,True
(D/'holdout_prepare.stdout').write_bytes(out)
(D/'holdout_prepare.stderr').write_bytes(err)
peak=resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss
result_path=D/'holdout_source.json'
complete=(not timed_out and code==0 and result_path.exists() and
          json.loads(result_path.read_text()).get('status')=='FROZEN_PROSPECTIVE_N131_SOURCE_HOLDOUT')
status=('COMPLETE' if complete and peak<protocol['rss_cap_bytes']
        else 'RSS_BOUNDARY' if peak>=protocol['rss_cap_bytes']
        else 'BOUNDED_UNKNOWN' if timed_out else 'PRODUCER_FAILURE')
receipt={'status':status,'protocol_sha256':sha(D/'holdout_prepare_protocol.json'),
         'runner_sha256':sha(Path(__file__)),'runtime_info_sha256':sha(D/'sage_runtime_info.json'),
         'command':command,'exit_code':code,'timed_out':timed_out,
         'wall_s':time.monotonic()-start,'peak_child_rss_bytes':peak,
         'stdout_sha256':sha(D/'holdout_prepare.stdout'),
         'stderr_sha256':sha(D/'holdout_prepare.stderr'),
         'source_sha256':sha(result_path) if complete else None}
(D/'holdout_prepare_receipt.json').write_text(json.dumps(receipt,sort_keys=True,indent=2)+'\n')
print(json.dumps({k:receipt[k] for k in ('status','wall_s','peak_child_rss_bytes','exit_code')}))
