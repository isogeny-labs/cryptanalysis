"""One-worker 600-second/4-GiB parent for the constructed-control check."""
import hashlib,json,resource,subprocess,time
from pathlib import Path
import psutil
h=Path(__file__).resolve().parent
p=json.loads((h/'n131_check_protocol.json').read_text())
def sha(q):return hashlib.sha256(q.read_bytes()).hexdigest()
assert sha(h/'run_n131_check.py')==p['runner_sha256']
assert not (h/'n131_check_receipt.json').exists()
start=time.monotonic_ns();before=resource.getrusage(resource.RUSAGE_CHILDREN)
parent=psutil.Process();peak=0;stop=None
with (h/'n131_check.stdout').open('x') as out,(h/'n131_check.stderr').open('x') as err:
    child=subprocess.Popen(['python3.12',str(h/'check_n131_control.py')],stdout=out,stderr=err)
    proc=psutil.Process(child.pid)
    while child.poll() is None:
        try:rss=parent.memory_info().rss+proc.memory_info().rss
        except psutil.NoSuchProcess:rss=parent.memory_info().rss
        peak=max(peak,rss)
        if rss>p['rss_cap_bytes']:stop='RSS_CAP'
        elif time.monotonic_ns()-start>=p['wall_cap_seconds']*10**9:stop='WALL_CAP'
        if stop:child.kill();break
        time.sleep(.05)
    code=child.wait()
end=time.monotonic_ns();after=resource.getrusage(resource.RUSAGE_CHILDREN)
result=h/'n131_control_check.json'
r={'status':'BOUNDED_UNKNOWN' if stop else 'PASS_CONSTRUCTED_CONTROL' if code==0 and result.exists() else 'ERROR',
   'stop_reason':stop,'exit_code':code,'worker_count':1,'parent_wall_ns':end-start,
   'peak_combined_rss_bytes_sampled':peak,'child_user_seconds':after.ru_utime-before.ru_utime,
   'child_system_seconds':after.ru_stime-before.ru_stime,'stdout_sha256':sha(h/'n131_check.stdout'),
   'stderr_sha256':sha(h/'n131_check.stderr'),'result_sha256':sha(result) if result.exists() else None,
   'protocol_sha256':sha(h/'n131_check_protocol.json')}
(h/'n131_check_receipt.json').write_text(json.dumps(r,sort_keys=True,indent=2)+'\n')
print(r['status'],(end-start)/1e9,peak,flush=True)
