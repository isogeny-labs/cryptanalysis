"""One-worker bounded exact group join for public bucket 905."""
import hashlib,json,resource,subprocess,time
from pathlib import Path
import psutil

HERE=Path(__file__).resolve().parent
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def main():
    p=json.loads((HERE/'bucket_join_protocol.json').read_text())
    paths={'runner':HERE/'run_bucket_join.py','source':HERE/'bucket_join.cpp',
           'binary':HERE/'bucket_join','group_source':HERE.parent/'n41_w8_ninepair_join_control_20261012/join9.cpp',
           'input':HERE.parent/'n131_w18_allseed_fourpair_20261012/n41_diagonal/pairs.tsv',
           'plan':HERE/'bucket_plan.json','long_receipt':HERE/'long_bucket_receipt.json'}
    assert {k:sha(v) for k,v in paths.items()}==p['sha256']
    assert json.loads(paths['plan'].read_text())['plan'][0]['bucket']==905
    assert not (HERE/'bucket_join_receipt.json').exists()
    start=time.monotonic_ns();before=resource.getrusage(resource.RUSAGE_CHILDREN)
    parent=psutil.Process();peak=0;stop=None
    with (HERE/'bucket_join.stdout').open('x') as out,(HERE/'bucket_join.stderr').open('x') as err:
        child=subprocess.Popen([str(paths['binary']),str(paths['input'])],stdout=out,stderr=err)
        proc=psutil.Process(child.pid)
        while child.poll() is None:
            now=time.monotonic_ns()
            try:rss=parent.memory_info().rss+proc.memory_info().rss
            except psutil.NoSuchProcess:rss=parent.memory_info().rss
            peak=max(peak,rss)
            if rss>p['rss_cap_bytes']:stop='RSS_CAP'
            elif (now-start)/1e9>=p['wall_cap_seconds']:stop='WALL_CAP'
            if stop:child.kill();break
            time.sleep(.05)
        code=child.wait()
    end=time.monotonic_ns();after=resource.getrusage(resource.RUSAGE_CHILDREN)
    lines=(HERE/'bucket_join.stdout').read_text().splitlines()
    setup=next((v for v in lines if v.startswith('SETUP ')),None)
    hit=next((v for v in lines if v.startswith('HIT ')),None)
    exhausted=next((v for v in lines if v.startswith('EXHAUSTED ')),None)
    status=('BOUNDED_UNKNOWN' if stop else 'HIT_PENDING_SAGE_AUDIT' if code==0 and hit
            else 'COMPLETE_EXHAUSTED' if code==0 and exhausted else 'ERROR')
    result={'status':status,'stop_reason':stop,'exit_code':code,'worker_count':1,
            'parent_wall_ns':end-start,'peak_combined_rss_bytes_sampled':peak,
            'child_user_seconds':after.ru_utime-before.ru_utime,
            'child_system_seconds':after.ru_stime-before.ru_stime,
            'setup_line':setup,'hit_line':hit,'exhausted_line':exhausted,
            'progress_lines':[v for v in lines if v.startswith('PROGRESS ')],
            'stdout_sha256':sha(HERE/'bucket_join.stdout'),
            'stderr_sha256':sha(HERE/'bucket_join.stderr'),
            'protocol_sha256':sha(HERE/'bucket_join_protocol.json')}
    (HERE/'bucket_join_receipt.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
    print(status,(end-start)/1e9,peak,flush=True)
if __name__=='__main__':main()
