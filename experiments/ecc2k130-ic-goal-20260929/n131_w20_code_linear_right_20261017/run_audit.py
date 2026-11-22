"""Monitor the independent full-candidate N131 membership replay."""
import hashlib,json,os,signal,subprocess,time
from pathlib import Path
import psutil

HERE=Path(__file__).resolve().parent
sha=lambda path:hashlib.sha256(Path(path).read_bytes()).hexdigest()
p=json.loads((HERE/'audit_protocol.json').read_text())
for path,digest in p['sources'].items():assert sha(path)==digest,path
command=[str(HERE/'audit'),p['fixture'],p['support'],p['valid_bitmap'],
         str(HERE/'audit_result.json'),str(p['native_cap_seconds']),str(p['rss_cap_bytes'])]
parent=psutil.Process(os.getpid())
start=time.monotonic();peak=0;stop=None;failures=0
with (HERE/'audit.stdout').open('x') as out,(HERE/'audit.stderr').open('x') as err:
    child=subprocess.Popen(command,stdout=out,stderr=err,start_new_session=True)
    proc=psutil.Process(child.pid)
    while child.poll() is None:
        try:peak=max(peak,parent.memory_info().rss+proc.memory_info().rss)
        except (psutil.NoSuchProcess,psutil.AccessDenied,PermissionError):
            if child.poll() is None:failures+=1
        if peak>p['rss_cap_bytes']:stop='RSS_CAP'
        elif time.monotonic()-start>p['parent_cap_seconds']:stop='PARENT_CAP'
        if stop:
            os.killpg(child.pid,signal.SIGTERM);break
        time.sleep(.1)
    child.wait()
try:result=json.loads((HERE/'audit_result.json').read_text())
except (FileNotFoundError,json.JSONDecodeError):result=None
status=('PASS' if child.returncode==0 and not stop and failures==0 and result and
        result['status']=='PASS_CODE_LINEAR_EQUIVALENCE'
        else 'BOUNDED_UNKNOWN' if stop else 'PRODUCER_FAILURE')
record={'status':status,'command':command,'exit_code':child.returncode,
        'stop_reason':stop,'monitor_failures':failures,
        'sampled_peak_combined_rss_bytes':peak,
        'parent_wall_seconds':time.monotonic()-start,
        'protocol_sha256':sha(HERE/'audit_protocol.json'),
        'stdout_sha256':sha(HERE/'audit.stdout'),
        'stderr_sha256':sha(HERE/'audit.stderr'),
        'audit_result_sha256':sha(HERE/'audit_result.json') if result else None}
with (HERE/'audit_receipt.json').open('x') as f:
    json.dump(record,f,sort_keys=True,indent=2);f.write('\n')
print(status,record['parent_wall_seconds'],peak,flush=True)
