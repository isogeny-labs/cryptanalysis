"""Resource-bound independent full pivotal-witness replay."""
import hashlib,json,resource,subprocess,time
from pathlib import Path
import psutil
h=Path(__file__).resolve().parent
p=json.loads((h/'audit_protocol.json').read_text())
def sha(q):return hashlib.sha256(q.read_bytes()).hexdigest()
paths={'source':h/'audit_rank.cpp','binary':h/'audit_rank','input':h.parent/'n131_w18_allseed_fourpair_20261012/n41_diagonal/pairs.tsv',
       'ranks':h/'ranks.tsv','witnesses':h/'witnesses.bin','producer_receipt':h/'rank_receipt.json','runner':h/'run_audit.py'}
assert {k:sha(v) for k,v in paths.items()}==p['sha256']
assert not (h/'audit_receipt.json').exists()
start=time.monotonic_ns();before=resource.getrusage(resource.RUSAGE_CHILDREN)
parent=psutil.Process();peak=0;stop=None
with (h/'audit.stdout').open('x') as out,(h/'audit.stderr').open('x') as err:
    child=subprocess.Popen([str(h/'audit_rank'),str(paths['input']),str(paths['ranks']),str(paths['witnesses'])],stdout=out,stderr=err)
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
line=next((x for x in (h/'audit.stdout').read_text().splitlines() if x.startswith('PASS_INDEPENDENT_LOW_PIVOT ')),None)
r={'status':'BOUNDED_UNKNOWN' if stop else 'PASS_INDEPENDENT_FULL_RANK_REPLAY' if code==0 and line else 'ERROR',
   'stop_reason':stop,'exit_code':code,'worker_count':1,'parent_wall_ns':end-start,
   'peak_combined_rss_bytes_sampled':peak,'child_user_seconds':after.ru_utime-before.ru_utime,
   'child_system_seconds':after.ru_stime-before.ru_stime,'summary_line':line,
   'stdout_sha256':sha(h/'audit.stdout'),'stderr_sha256':sha(h/'audit.stderr'),
   'protocol_sha256':sha(h/'audit_protocol.json')}
(h/'audit_receipt.json').write_text(json.dumps(r,sort_keys=True,indent=2)+'\n')
print(r['status'],(end-start)/1e9,peak,flush=True)
