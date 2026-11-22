"""One-worker parent cap for the frozen dual-norm circuit build."""
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
assert protocol['producer_sha256']==sha(D/'build.py')
assert (D/'sage_runtime_info.json').exists()
command=['/Volumes/SSD990/cryptanalysis/sage','-python',str(D/'build.py')]
start=time.monotonic()
try:
    proc=subprocess.run(command,capture_output=True,timeout=protocol['wall_cap_s'])
    stdout,stderr,code,timed_out=proc.stdout,proc.stderr,proc.returncode,False
except subprocess.TimeoutExpired as exc:
    stdout,stderr,code,timed_out=exc.stdout or b'',exc.stderr or b'',None,True
(D/'build_retry.stdout').write_bytes(stdout)
(D/'build_retry.stderr').write_bytes(stderr)
peak=resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss
result=D/'build_result.json'
complete=(not timed_out and code==0 and result.exists() and
          json.loads(result.read_text()).get('status')=='N41_DUAL_NORM_PUBLIC_CIRCUIT_CONTROL_PASS')
status=('COMPLETE' if complete and peak<protocol['rss_cap_bytes']
        else 'RSS_BOUNDARY' if peak>=protocol['rss_cap_bytes']
        else 'BOUNDED_UNKNOWN' if timed_out else 'PRODUCER_FAILURE')
receipt={'status':status,'protocol_sha256':sha(D/'protocol.json'),
         'runner_sha256':sha(Path(__file__)),'command':command,
         'exit_code':code,'timed_out':timed_out,'parent_wall_s':time.monotonic()-start,
         'peak_child_rss_bytes':peak,
         'runtime_info_sha256':sha(D/'sage_runtime_info.json'),
         'stdout_sha256':sha(D/'build_retry.stdout'),
         'stderr_sha256':sha(D/'build_retry.stderr'),
         'build_result_sha256':sha(result) if complete else None}
(D/'build_retry_receipt.json').write_text(json.dumps(receipt,sort_keys=True,indent=2)+'\n')
print(json.dumps({k:receipt[k] for k in ('status','parent_wall_s',
                                          'peak_child_rss_bytes','exit_code')}))
