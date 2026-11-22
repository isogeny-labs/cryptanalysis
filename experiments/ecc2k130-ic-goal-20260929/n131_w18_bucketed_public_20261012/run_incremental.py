"""Resource-bound incremental solver parent, with terminal receipt."""
import hashlib,json,resource,subprocess,time
from pathlib import Path
import psutil

HERE=Path(__file__).resolve().parent
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def save(path,obj):
    tmp=path.with_suffix('.tmp');tmp.write_text(json.dumps(obj,sort_keys=True,indent=2)+'\n');tmp.replace(path)
def main():
    p=json.loads((HERE/'incremental_protocol.json').read_text())
    paths={'runner':HERE/'run_incremental.py','worker':HERE/'incremental_worker.py',
           'plan':HERE/'bucket_plan.json','base_formula':HERE.parent/'n131_w18_joint_pair_filter_20261012/ordinary.xcnf',
           'module':Path(p['pycryptosat_module_path']),'python':Path(p['python_path']).resolve()}
    assert {k:sha(v) for k,v in paths.items()}==p['sha256']
    assert not (HERE/'incremental_receipt.json').exists()
    save(HERE/'incremental_started.json',{'status':'STARTED','protocol_sha256':sha(HERE/'incremental_protocol.json'),
                                          'start_wall_ns':time.time_ns()})
    start=time.monotonic_ns();before=resource.getrusage(resource.RUSAGE_CHILDREN)
    parent=psutil.Process();peak=0;stop=None
    with (HERE/'incremental.stdout').open('x') as out,(HERE/'incremental.stderr').open('x') as err:
        child=subprocess.Popen([p['python_path'],str(paths['worker'])],stdout=out,stderr=err)
        proc=psutil.Process(child.pid)
        while child.poll() is None:
            now=time.monotonic_ns()
            try:rss=parent.memory_info().rss+proc.memory_info().rss
            except psutil.NoSuchProcess:rss=parent.memory_info().rss
            peak=max(peak,rss)
            if rss>p['rss_cap_bytes']:stop='RSS_CAP'
            elif (now-start)/1e9>=p['overall_wall_cap_seconds']:stop='WALL_CAP'
            if stop:child.kill();break
            time.sleep(.05)
        code=child.wait()
    end=time.monotonic_ns();after=resource.getrusage(resource.RUSAGE_CHILDREN)
    progress_path=HERE/'incremental_progress.json'
    progress=json.loads(progress_path.read_text()) if progress_path.exists() else None
    attempts=[] if progress is None else progress['attempts']
    lines=(HERE/'incremental.stdout').read_text().splitlines()
    terminal=any(x.startswith('WORKER_DONE ') for x in lines)
    status=('SAT_PENDING_MODEL_AUDIT' if any(x['status']=='SAT_PENDING_MODEL_AUDIT' for x in attempts)
            else 'BOUNDED_UNKNOWN' if stop or any(x['status']=='BOUNDED_UNKNOWN' for x in attempts)
            else 'COMPLETE_NO_MODEL_IN_EIGHT_BUCKETS' if code==0 and terminal and len(attempts)==8
            else 'ERROR')
    r={'status':status,'stop_reason':stop,'exit_code':code,'worker_count':1,
       'attempts':attempts,'parent_wall_ns':end-start,'peak_combined_rss_bytes_sampled':peak,
       'child_user_seconds':after.ru_utime-before.ru_utime,
       'child_system_seconds':after.ru_stime-before.ru_stime,
       'setup_ns':None if progress is None else progress['setup_ns'],
       'stdout_sha256':sha(HERE/'incremental.stdout'),'stderr_sha256':sha(HERE/'incremental.stderr'),
       'progress_sha256':sha(progress_path) if progress_path.exists() else None,
       'model_sha256':sha(HERE/'incremental_model.json') if (HERE/'incremental_model.json').exists() else None,
       'protocol_sha256':sha(HERE/'incremental_protocol.json')}
    save(HERE/'incremental_receipt.json',r)
    print(status,len(attempts),(end-start)/1e9,peak,flush=True)

if __name__=='__main__':main()
