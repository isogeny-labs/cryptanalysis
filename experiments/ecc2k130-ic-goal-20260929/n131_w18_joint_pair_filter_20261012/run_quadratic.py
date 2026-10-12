"""Resource-bounded exact equal-seed quadratic feature-rank census."""
import hashlib,json,resource,subprocess,time
from pathlib import Path
import psutil
h=Path(__file__).resolve().parent
p=json.loads((h/'quadratic_protocol.json').read_text())
def sha(q):return hashlib.sha256(q.read_bytes()).hexdigest()
paths={'source':h/'quadratic_rank.cpp','binary':h/'quadratic_rank',
       'input':h.parent/'n131_w18_allseed_fourpair_20261012/n41_diagonal/pairs.tsv',
       'group_source':h.parent/'n41_w8_ninepair_join_control_20261012/join9.cpp',
       'runner':h/'run_quadratic.py'}
assert {k:sha(v) for k,v in paths.items()}==p['sha256']
assert not (h/'quadratic_receipt.json').exists()
start=time.monotonic_ns();before=resource.getrusage(resource.RUSAGE_CHILDREN)
parent=psutil.Process();peak=0;stop=None
with (h/'quadratic.stdout').open('x') as out,(h/'quadratic.stderr').open('x') as err:
    child=subprocess.Popen([str(h/'quadratic_rank'),str(paths['input']),str(h/'quadratic_ranks.tsv')],stdout=out,stderr=err)
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
line=next((x for x in (h/'quadratic.stdout').read_text().splitlines() if x.startswith('QUADRATIC_RANK ')),None)
r={'status':'BOUNDED_UNKNOWN' if stop else 'COMPLETE_QUADRATIC_RANK_CENSUS' if code==0 and line else 'ERROR',
   'stop_reason':stop,'exit_code':code,'worker_count':1,'parent_wall_ns':end-start,
   'peak_combined_rss_bytes_sampled':peak,'child_user_seconds':after.ru_utime-before.ru_utime,
   'child_system_seconds':after.ru_stime-before.ru_stime,'summary_line':line,
   'output_sha256':sha(h/'quadratic_ranks.tsv') if (h/'quadratic_ranks.tsv').exists() else None,
   'stdout_sha256':sha(h/'quadratic.stdout'),'stderr_sha256':sha(h/'quadratic.stderr'),
   'protocol_sha256':sha(h/'quadratic_protocol.json')}
(h/'quadratic_receipt.json').write_text(json.dumps(r,sort_keys=True,indent=2)+'\n')
print(r['status'],(end-start)/1e9,peak,flush=True)
