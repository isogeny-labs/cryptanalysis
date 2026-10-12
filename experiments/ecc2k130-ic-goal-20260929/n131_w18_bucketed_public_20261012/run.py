"""Sequential one-worker search of frozen public-point source buckets."""
import hashlib,json,resource,subprocess,time
from pathlib import Path
import psutil

HERE=Path(__file__).resolve().parent
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def save(path,obj):
    tmp=path.with_suffix('.tmp')
    tmp.write_text(json.dumps(obj,indent=2,sort_keys=True)+'\n')
    tmp.replace(path)

def main():
    p=json.loads((HERE/'solver_protocol.json').read_text())
    paths={'runner':HERE/'run.py','plan':HERE/'bucket_plan.json',
           'solver':Path(p['solver_path'])}
    assert {k:sha(v) for k,v in paths.items()}==p['sha256']
    plan=json.loads(paths['plan'].read_text())
    assert plan['status']=='FROZEN_BUCKET_FORMULAS'
    assert len(plan['plan'])==p['attempts']==8
    for row in plan['plan']:
        assert sha(HERE/f"bucket_{row['rank']:02}.xcnf")==row['formula_sha256']
    assert not (HERE/'search_receipt.json').exists()
    save(HERE/'search_started.json',{'status':'STARTED','solver_protocol_sha256':sha(HERE/'solver_protocol.json'),
                                    'plan_sha256':sha(paths['plan']),'start_wall_ns':time.time_ns()})
    total_start=time.monotonic_ns();before=resource.getrusage(resource.RUSAGE_CHILDREN)
    parent=psutil.Process();peak=0;attempts=[];stop=None
    for row in plan['plan']:
        if (time.monotonic_ns()-total_start)/1e9>=p['overall_wall_cap_seconds']:
            stop='OVERALL_WALL_CAP';break
        rank=row['rank'];formula=HERE/f'bucket_{rank:02}.xcnf'
        outpath=HERE/f'bucket_{rank:02}.stdout';errpath=HERE/f'bucket_{rank:02}.stderr'
        with outpath.open('x') as out,errpath.open('x') as err:
            launched=time.monotonic_ns()
            child=subprocess.Popen([p['solver_path'],*p['solver_flags'],str(formula)],stdout=out,stderr=err)
            start=time.monotonic_ns();proc=psutil.Process(child.pid);bucket_stop=None
            while child.poll() is None:
                now=time.monotonic_ns()
                try:rss=parent.memory_info().rss+proc.memory_info().rss
                except psutil.NoSuchProcess:rss=parent.memory_info().rss
                peak=max(peak,rss)
                if rss>p['rss_cap_bytes']:bucket_stop='RSS_CAP'
                elif (now-start)/1e9>=p['per_bucket_parent_cap_seconds']:
                    bucket_stop='BUCKET_WALL_CAP'
                elif (now-total_start)/1e9>=p['overall_wall_cap_seconds']:
                    bucket_stop='OVERALL_WALL_CAP'
                if bucket_stop:child.kill();break
                time.sleep(.05)
            code=child.wait();ended=time.monotonic_ns()
        lines=outpath.read_text().splitlines()
        terminal=[line for line in lines if line.startswith('s ')]
        status=('BOUNDED_UNKNOWN' if bucket_stop else
                'SAT_PENDING_MODEL_AUDIT' if 's SATISFIABLE' in terminal else
                'UNSAT' if 's UNSATISFIABLE' in terminal else
                'BOUNDED_UNKNOWN' if 's INDETERMINATE' in terminal else 'ERROR')
        attempt={'rank':rank,'bucket':row['bucket'],'low6_masks':row['low6_masks'],
                 'status':status,'stop_reason':bucket_stop,'exit_code':code,
                 'solver_terminal_lines':terminal,'launch_ns':start-launched,
                 'solver_wall_ns':ended-start,'stdout_sha256':sha(outpath),
                 'stderr_sha256':sha(errpath),'formula_sha256':sha(formula)}
        attempts.append(attempt)
        save(HERE/'search_progress.json',{'status':'RUNNING','attempts':attempts,
                                          'peak_combined_rss_bytes_sampled':peak})
        if status=='SAT_PENDING_MODEL_AUDIT' or bucket_stop in ('RSS_CAP','OVERALL_WALL_CAP'):
            stop=bucket_stop;break
    ended=time.monotonic_ns();after=resource.getrusage(resource.RUSAGE_CHILDREN)
    final=('SAT_PENDING_MODEL_AUDIT' if attempts and attempts[-1]['status']=='SAT_PENDING_MODEL_AUDIT'
           else 'BOUNDED_UNKNOWN' if stop or any(x['status']=='BOUNDED_UNKNOWN' for x in attempts)
           else 'COMPLETE_NO_MODEL_IN_EIGHT_BUCKETS')
    receipt={'status':final,'stop_reason':stop,'worker_count':1,'attempts':attempts,
             'parent_wall_ns':ended-total_start,'prepare_wall_ns':plan['prepare_wall_ns'],
             'peak_combined_rss_bytes_sampled':peak,
             'child_user_seconds':after.ru_utime-before.ru_utime,
             'child_system_seconds':after.ru_stime-before.ru_stime,
             'solver_protocol_sha256':sha(HERE/'solver_protocol.json'),
             'plan_sha256':sha(paths['plan'])}
    save(HERE/'search_receipt.json',receipt)
    print(final,len(attempts),(ended-total_start)/1e9,peak,flush=True)

if __name__=='__main__':main()
