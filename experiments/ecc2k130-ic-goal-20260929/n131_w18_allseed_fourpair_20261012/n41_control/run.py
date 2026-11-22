"""One-worker bounded four-pair public-point join with frozen sources."""
import hashlib,json,resource,subprocess,time
from pathlib import Path
import psutil
h=Path(__file__).resolve().parent
p=json.loads((h/'protocol.json').read_text())
def sha(q):return hashlib.sha256(q.read_bytes()).hexdigest()
paths={'source':h/'join4.cpp','binary':h/'join4','input':h/'pairs.tsv',
       'source_export':h/'prepare_result.json','runner':h/'run.py',
       'group_source':h.parent.parent/'n41_w8_ninepair_join_control_20261012/join9.cpp'}
assert {k:sha(v) for k,v in paths.items()}==p['sha256']
assert p['status']=='FROZEN_N41_ALLSEED_FOURPAIR_JOIN' and not (h/'receipt.json').exists()
start=time.monotonic_ns();before=resource.getrusage(resource.RUSAGE_CHILDREN)
parent=psutil.Process();peak=0;stop=None
with (h/'stdout.log').open('x') as out,(h/'stderr.log').open('x') as err:
    child=subprocess.Popen([str(h/'join4'),str(h/'pairs.tsv')],stdout=out,stderr=err)
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
lines=(h/'stdout.log').read_text().splitlines()
key=lambda s:next((line for line in lines if line.startswith(s)),None)
receipt={'status':'BOUNDED_UNKNOWN' if stop else 'HIT_PENDING_INDEPENDENT_REPLAY' if code==0 and key('HIT ') else 'EXHAUSTED' if code==0 and key('EXHAUSTED ') else 'ERROR',
         'exit_code':code,'stop_reason':stop,'worker_count':1,'runner_wall_ns':end-start,
         'child_user_seconds':after.ru_utime-before.ru_utime,'child_system_seconds':after.ru_stime-before.ru_stime,
         'peak_combined_rss_bytes_sampled':peak,'left_line':key('LEFT_DONE '),'hit_line':key('HIT '),
         'exhausted_line':key('EXHAUSTED '),'stdout_sha256':sha(h/'stdout.log'),
         'stderr_sha256':sha(h/'stderr.log'),'protocol_sha256':sha(h/'protocol.json')}
(h/'receipt.json').write_text(json.dumps(receipt,sort_keys=True,indent=2)+'\n')
print(receipt['status'],(end-start)/1e9,peak)
