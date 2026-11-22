"""Resource-bound one-worker runner for v2 circuit build and control replay."""
import hashlib,json,resource,subprocess,sys,time
from pathlib import Path
import psutil
h=Path(__file__).resolve().parent;mode=sys.argv[1]
assert mode in ('n41_control','n131_control','n131_public')
p=json.loads((h/'v2_protocol.json').read_text())
def sha(q):return hashlib.sha256(q.read_bytes()).hexdigest()
assert sha(h/'v2_run.py')==p['runner_sha256']
result=h/('v2_'+mode+'.json');receipt=h/('v2_'+mode+'_receipt.json')
assert not receipt.exists()
start=time.monotonic_ns();before=resource.getrusage(resource.RUSAGE_CHILDREN)
parent=psutil.Process();peak=0;stop=None
with (h/('v2_'+mode+'.stdout')).open('x') as out,(h/('v2_'+mode+'.stderr')).open('x') as err:
    child=subprocess.Popen(['python3.12',str(h/'v2_build.py'),mode],stdout=out,stderr=err)
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
r={'status':'BOUNDED_UNKNOWN' if stop else 'PASS' if code==0 and result.exists() else 'ERROR',
   'mode':mode,'stop_reason':stop,'exit_code':code,'worker_count':1,
   'parent_wall_ns':end-start,'peak_combined_rss_bytes_sampled':peak,
   'child_user_seconds':after.ru_utime-before.ru_utime,
   'child_system_seconds':after.ru_stime-before.ru_stime,
   'stdout_sha256':sha(h/('v2_'+mode+'.stdout')),
   'stderr_sha256':sha(h/('v2_'+mode+'.stderr')),
   'result_sha256':sha(result) if result.exists() else None,
   'protocol_sha256':sha(h/'v2_protocol.json')}
receipt.write_text(json.dumps(r,sort_keys=True,indent=2)+'\n')
print(r['status'],mode,(end-start)/1e9,peak,flush=True)
