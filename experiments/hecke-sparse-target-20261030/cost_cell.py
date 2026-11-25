"""Fixed-base preparation workload for an accepted CUDA benchmark host.

The script emits raw exclusive phase costs and no qualified speed ratio.
"""
import argparse
import hashlib
import json
from math import isqrt
from pathlib import Path
import resource
import signal
import subprocess
import time

from modular import Curve,Modular
from pair_reuse import harvest,check_index
from study import collect_rows,collapse,reduced
from verify import ShortCurve,rank as independent_rank

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]


def cuda_devices():
    try:
        run=subprocess.run(['nvidia-smi','--query-gpu=uuid,name','--format=csv,noheader'],
                           text=True,capture_output=True,timeout=15)
    except (OSError,subprocess.TimeoutExpired) as error:
        raise RuntimeError('No accessible CUDA benchmark device') from error
    devices=[row.strip() for row in run.stdout.splitlines() if row.strip()]
    if run.returncode or not devices:
        raise RuntimeError('No accessible CUDA benchmark device')
    return devices


class TunedBSGS:
    def __init__(self,curve,G,r,free_logs,cap=4096):
        self.curve,self.G,self.r=curve,G,r
        self.m=min(cap,r,max(1,isqrt(r*free_logs//2)+1))
        self.table={};point=None
        for j in range(self.m):
            self.table.setdefault(point,j);point=curve.add(point,G)
        self.stride=curve.neg(point)

    def log(self,P):
        current=P
        for i in range((self.r+self.m-1)//self.m+1):
            if current in self.table:
                result=(i*self.m+self.table[current])%self.r
                assert self.curve.mul(result,self.G)==P
                return result
            current=self.curve.add(current,self.stride)
        raise AssertionError('Point outside declared subgroup')


def record_phase(progress,name,operation,curve):
    wall=time.perf_counter();cpu=time.process_time();ops=curve.ops
    progress['benchmark_executed']=True
    try:
        value=operation()
    except BaseException:
        progress['interrupted_phase']=dict(name=name,complete=False,
            wall_seconds_until_interruption=time.perf_counter()-wall,
            cpu_seconds_until_interruption=time.process_time()-cpu,
            group_addition_calls_until_interruption=curve.ops-ops)
        raise
    progress['phases'][name]=dict(wall_seconds=time.perf_counter()-wall,
        cpu_seconds=time.process_time()-cpu,group_addition_calls=curve.ops-ops)
    return value


def run_cell(arm,progress=None):
    if progress is None:progress={'benchmark_executed':False,'phases':{}}
    source=HERE/'runs/f6-large-01/receipt.json'
    data=json.loads(source.read_text());p,r,h=data['p'],data['r'],data['h']
    assert (p,r,h)==(1032607,206477,5)
    base=[tuple(P) for P in data['normalized_base']]
    raw=[tuple(P) for P in data['raw_points']]
    G=tuple(data['curve']['generator']);curve=Curve(p);phases=progress['phases']
    progress.update(input_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
                    identity=data['identity'],p=p,r=r,
                    source_hashes={name:hashlib.sha256((HERE/name).read_bytes()).hexdigest()
                                   for name in ['cost_cell.py','COST_CELL_PROTOCOL.md','pair_reuse.py','modular.py','study.py','verify.py']})
    def phase(name,operation):
        return record_phase(progress,name,operation,curve)
    start=time.perf_counter();start_cpu=time.process_time()
    if arm=='hecke':
        def geometry():
            modular=Modular(p,[2,3]);modular.curve=curve
            rows,_,_,_,_=collect_rows(modular,raw,[2,3])
            projected=[curve.mul(h,P) for P in raw]
            columns,folded=collapse(projected,rows,curve,True)
            assert columns==base
            return folded
        geometric=phase('geometric_function_and_fiber_construction',geometry)
    else:
        geometric=[]
        phases['geometric_function_and_fiber_construction']=dict(wall_seconds=0,cpu_seconds=0,group_addition_calls=0,status='not used by generic method')
    _,index=phase('pair_index_and_collision_handling',lambda:harvest(base,curve,r))
    rows=geometric+index['basis_rows']
    rref,pivots=phase('relation_linear_algebra',lambda:reduced(rows,len(base),r))
    free=[i for i in range(len(base)) if i not in pivots]
    solver=phase('bsgs_table',lambda:TunedBSGS(curve,G,r,len(free)))
    logs=[0]*len(base)
    def solve_free():
        for i in free:logs[i]=solver.log(base[i])
    phase('generic_free_log_queries',solve_free)
    def recover():
        for row,pivot in zip(rref,pivots):logs[pivot]=-sum(int(row[i])*logs[i] for i in free)%r
    phase('pivot_recovery',recover)
    def replay():
        assert logs==data['base_logs']
        short=ShortCurve(p);g=short.point(G)
        assert all(short.times(k,g)==short.point(P) for k,P in zip(logs,base))
    phase('prepared_label_replay',replay)
    total=time.perf_counter()-start;total_cpu=time.process_time()-start_cpu
    overhead=total-sum(value['wall_seconds'] for value in phases.values())
    overhead_cpu=total_cpu-sum(value['cpu_seconds'] for value in phases.values())
    phases['residual_overhead']=dict(wall_seconds=overhead,cpu_seconds=overhead_cpu,group_addition_calls=0)
    progress.update(preparation_wall_seconds=total,preparation_cpu_seconds=total_cpu)
    certificate_wall=time.perf_counter();certificate_cpu=time.process_time()
    certificate=check_index(base,r,index,p)
    assert independent_rank(rows,len(base),r)==len(pivots)
    certificate.update(wall_seconds=time.perf_counter()-certificate_wall,
                       cpu_seconds=time.process_time()-certificate_cpu,
                       scope='outside preparation window; actual label replay remains inside')
    return dict(status='verified_raw_cost_cell',arm=arm,p=p,r=r,identity=data['identity'],
                free_logs=len(free),bsgs_entries=solver.m,bsgs_entry_cap=4096,
                phases=phases,preparation_wall_seconds=total,preparation_cpu_seconds=total_cpu,
                certificate=certificate,peak_process_rss_platform_units=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                input_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
                source_hashes={name:hashlib.sha256((HERE/name).read_bytes()).hexdigest()
                               for name in ['cost_cell.py','COST_CELL_PROTOCOL.md','pair_reuse.py','modular.py','study.py','verify.py']},
                accepted_harness_receipt=None,qualified_speedup=None,
                scope='Fixed supplied-base preparation; excludes imports/input loading and full base generation')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--arm',choices=['generic','hecke'],required=True)
    parser.add_argument('--out',type=Path,required=True);args=parser.parse_args()
    subprocess.run(['bash','scripts/checkpoint.sh','gate'],cwd=ROOT,check=True)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    # Reserve unique output before any workload; never overwrite another row.
    with args.out.open('x') as output:
        try:
            devices=cuda_devices()
        except RuntimeError as error:
            result=dict(status='blocked_no_cuda_host',arm=args.arm,reason=str(error),benchmark_executed=False)
            code=2
        else:
            progress=dict(benchmark_executed=False,phases={},qualified_speedup=None,
                          accepted_harness_receipt=None)
            def timeout(*_):raise TimeoutError('600-second cost-cell cap')
            previous_handler=signal.getsignal(signal.SIGALRM)
            signal.signal(signal.SIGALRM,timeout)
            attempt_wall=time.perf_counter();attempt_cpu=time.process_time()
            try:
                signal.alarm(600)
                result=run_cell(args.arm,progress)
                code=0
            except BaseException as error:
                code=124 if isinstance(error,TimeoutError) else 130 if isinstance(error,KeyboardInterrupt) else 1
                status='cost_cell_timeout' if code==124 else 'cost_cell_interrupted' if code==130 else 'cost_cell_failed'
                result=dict(progress,status=status,arm=args.arm,error_type=type(error).__name__,
                            reason=str(error),preparation_wall_seconds=progress.get('preparation_wall_seconds'),
                            preparation_cpu_seconds=progress.get('preparation_cpu_seconds'),
                            peak_process_rss_platform_units=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                            attempt_wall_seconds=time.perf_counter()-attempt_wall,
                            attempt_cpu_seconds=time.process_time()-attempt_cpu,
                            timing_scope='Failure attempt includes input loading; completed phases and any available preparation totals are retained separately.')
            finally:
                signal.alarm(0)
                signal.signal(signal.SIGALRM,previous_handler)
            result['gpu_devices']=devices
        output.write(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps(result),flush=True)
    raise SystemExit(code)


if __name__=='__main__':main()
