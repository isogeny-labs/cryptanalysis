"""One-worker full-cap public search with exact first-pair reciprocal gate."""
import hashlib,json,resource,subprocess,time
from pathlib import Path
import psutil

HERE=Path(__file__).resolve().parent
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def main():
    p=json.loads((HERE/'table_solver_protocol.json').read_text())
    paths={'runner':HERE/'run_table_bucket.py','formula':HERE/'bucket_00_table.xcnf',
           'plan':HERE/'bucket_plan.json','solver':Path(p['solver_path']),
           'table_result':HERE/'table_gate_result.json',
           'parser_control':HERE/'parser_control_result.json'}
    assert {k:sha(v) for k,v in paths.items()}==p['sha256']
    plan=json.loads(paths['plan'].read_text())
    assert plan['plan'][0]['bucket']==905
    assert sha(paths['formula'])==json.loads(paths['table_result'].read_text())['formula_sha256']
    assert json.loads(paths['parser_control'].read_text())['status']=='PASS_PYCRYPTOSAT_FULL_MODEL_REPLAY'
    assert not (HERE/'table_solver_receipt.json').exists()
    start=time.monotonic_ns();before=resource.getrusage(resource.RUSAGE_CHILDREN)
    parent=psutil.Process();peak=0;stop=None
    with (HERE/'table_solver.stdout').open('x') as out,(HERE/'table_solver.stderr').open('x') as err:
        child=subprocess.Popen([p['solver_path'],*p['solver_flags'],str(paths['formula'])],stdout=out,stderr=err)
        launched=time.monotonic_ns();proc=psutil.Process(child.pid)
        while child.poll() is None:
            now=time.monotonic_ns()
            try:rss=parent.memory_info().rss+proc.memory_info().rss
            except psutil.NoSuchProcess:rss=parent.memory_info().rss
            peak=max(peak,rss)
            if rss>p['rss_cap_bytes']:stop='RSS_CAP'
            elif (now-start)/1e9>=p['parent_wall_cap_seconds']:stop='WALL_CAP'
            if stop:child.kill();break
            time.sleep(.05)
        code=child.wait()
    end=time.monotonic_ns();after=resource.getrusage(resource.RUSAGE_CHILDREN)
    terminal=[v for v in (HERE/'table_solver.stdout').read_text().splitlines() if v.startswith('s ')]
    status=('BOUNDED_UNKNOWN' if stop else 'SAT_PENDING_MODEL_AUDIT' if 's SATISFIABLE' in terminal
            else 'UNSAT' if 's UNSATISFIABLE' in terminal else 'BOUNDED_UNKNOWN'
            if 's INDETERMINATE' in terminal else 'ERROR')
    result={'status':status,'stop_reason':stop,'exit_code':code,'bucket':905,'worker_count':1,
            'parent_wall_ns':end-start,'launch_ns':launched-start,
            'solver_wall_ns':end-launched,'peak_combined_rss_bytes_sampled':peak,
            'child_user_seconds':after.ru_utime-before.ru_utime,
            'child_system_seconds':after.ru_stime-before.ru_stime,
            'solver_terminal_lines':terminal,'stdout_sha256':sha(HERE/'table_solver.stdout'),
            'stderr_sha256':sha(HERE/'table_solver.stderr'),
            'protocol_sha256':sha(HERE/'table_solver_protocol.json')}
    (HERE/'table_solver_receipt.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
    print(status,(end-start)/1e9,peak,flush=True)
if __name__=='__main__':main()
