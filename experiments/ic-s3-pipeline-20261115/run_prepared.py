#!/usr/bin/env python3
"""Fixed public-instance IC panel; retains caps and unqualified host evidence."""
import hashlib
import json
import os
from pathlib import Path
import platform
import resource
import shutil
import signal
import subprocess
import time
import tarfile

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
OUT=HERE/'timing-001'
OUT.mkdir(exist_ok=False)
START=time.monotonic()
METHODS=['buchberger-f2','f4-f2','fes-f2-wide','mitm']


def read(p):
    try:return Path(p).read_text()
    except OSError:return None


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def snap():
    return {p:read(p) for p in ['/proc/self/status','/proc/self/cgroup','/proc/self/mountinfo',
            '/proc/stat','/proc/self/numa_maps','/sys/fs/cgroup/cpu.stat','/sys/fs/cgroup/memory.events',
            '/sys/fs/cgroup/cpu/cpu.stat','/sys/fs/cgroup/memory/memory.failcnt']}


def command(args,timeout,env=None):
    remaining=780-(time.monotonic()-START)
    if remaining<=0:raise TimeoutError('controller soft limit')
    started=time.monotonic()
    p=subprocess.Popen(args,cwd=ROOT,env=env,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True)
    try:out,err=p.communicate(timeout=min(timeout,remaining))
    except subprocess.TimeoutExpired:
        os.killpg(p.pid,signal.SIGKILL);out,err=p.communicate()
        return 124,out,err+'\nprocess group killed at budget\n',time.monotonic()-started
    return p.returncode,out,err,time.monotonic()-started


sources=['suite/examples/ic_s3_pipeline_probe.rs','suite/Cargo.toml','suite/Cargo.lock',
         'suite/src/cryptanalysis/pq_descent_symbolic.rs','suite/src/cryptanalysis/ic_framework/mod.rs',
         'suite/src/cryptanalysis/ic_framework/plugins.rs','suite/src/cryptanalysis/ic_boundary.rs',
         'suite/src/cryptanalysis/ic_framework/solvers.rs',
         str(HERE.relative_to(ROOT)/'run_prepared.py'),str(HERE.relative_to(ROOT)/'PROTOCOL.md'),
         str(HERE.relative_to(ROOT)/'instances.json'),str(HERE.relative_to(ROOT)/'identities.json'),str(HERE.relative_to(ROOT)/'prepared-input.json'),str(HERE.relative_to(ROOT)/'PREPARED_TIMING_PROTOCOL.md')]
host={'platform':platform.platform(),'cpuinfo':read('/proc/cpuinfo'),'initial':snap(),
      'allowed_cpus':sorted(os.sched_getaffinity(0)), 'rustc':subprocess.check_output(['rustc','-Vv'],text=True),
      'source_sha256':{p:sha(ROOT/p) for p in sources},'placement':'unqualified gVisor; CPU work on L4 allocation'}
binaries={};pairs=[];references=[];arms=[]
identities=json.loads((HERE/'identities.json').read_text())


def arm(variant,index,method,fixture,role):
    args=[binaries[variant],str(HERE/'instances.json'),str(index),method,str(fixture)]
    before=snap();usage=resource.getrusage(resource.RUSAGE_CHILDREN)
    code,out,err,wall=command(args,12)
    after=resource.getrusage(resource.RUSAGE_CHILDREN)
    row={'variant':variant,'index':index,'method':method,'fixture':fixture,'role':role,'argv':args,
         'exit_code':code,'stdout':out,'stderr':err,'process_wall_s':wall,'before':before,'after':snap(),
         'cpu_s':after.ru_utime+after.ru_stime-usage.ru_utime-usage.ru_stime,
         'involuntary':after.ru_nivcsw-usage.ru_nivcsw,'qualified':None}
    if code==0:
        try:row['result']=json.loads(out)
        except ValueError:row['parse_error']=True
    with (OUT/'arms.jsonl').open('a') as f:f.write(json.dumps(row)+'\n')
    arms.append(row)
    return row


def report(row):return row.get('result',{}).get('report',{}).get('Ok')


def cold(row):
    r=report(row)
    return None if r is None else row['result']['context_ns']*1e-9+r['wall_seconds']


def checkpoint():
    (OUT/'pairs.json').write_text(json.dumps(pairs,indent=2)+'\n')
    (OUT/'references.json').write_text(json.dumps(references,indent=2)+'\n')


try:
    prepared=json.loads((HERE/'prepared-input.json').read_text())
    archive=Path('/jobs')/prepared['source_job']/'shards/0/out.tar.gz'
    with tarfile.open(archive,'r:gz') as tar:
        prefix='experiments/ic-s3-pipeline-20261115/build-001/'
        receipt_bytes=tar.extractfile(prefix+'receipt.json').read()
        assert hashlib.sha256(receipt_bytes).hexdigest()==prepared['receipt_sha256']
        receipt=json.loads(receipt_bytes)
        assert receipt['status']=='prepared' and receipt['source_commit']==prepared['source_commit']
        first_candidate=json.loads((ROOT/'experiments/ic-bench/candidates'/(identities['0']['buchberger-f2']['reference']+'.json')).read_text())
        assert receipt['source_sha256']==first_candidate['implementation']['sources_sha256']
        for variant in ['reference','direct']:
            data=tar.extractfile(prefix+'probe-'+variant).read()
            expected=prepared['binary_sha256'][variant]
            assert hashlib.sha256(data).hexdigest()==expected==receipt['binaries'][variant]['sha256']
            binary=OUT/('probe-'+variant);binary.write_bytes(data);binary.chmod(0o755)
            binaries[variant]=str(binary)
        (OUT/'preparation-receipt.json').write_bytes(receipt_bytes)
    host['binary_source_commit']=receipt['source_commit']
    host['binary_toolchain']=receipt['rustc']
    host['binary_sha256']={v:sha(p) for v,p in binaries.items()}
    os.sched_setaffinity(0,{host['allowed_cpus'][0]});host['selected_cpu']=host['allowed_cpus'][0]
    for fixture in range(100,106):
        for index in [0,1]:
            reference=arm('reference',index,'rho',fixture,'matched-reference')
            references.append(reference);checkpoint()
            offset=(fixture-100)%len(METHODS)
            for method in METHODS[offset:]+METHODS[:offset]:
                pre=arm('reference',index,'mitm',0,'calibration')
                order=['reference','direct'] if fixture%2==0 else ['direct','reference']
                runs={v:arm(v,index,method,fixture,'pipeline') for v in order}
                post=arm('reference',index,'mitm',0,'calibration')
                pair={'index':index,'fixture':fixture,'method':method,'order':order,'runs':runs,
                      'pre':pre,'post':post,'qualified':None,
                      'identities':identities[str(index)][method],
                      'workload':identities[str(index)]['workloads'][str(fixture)]}
                a,b=(report(runs[v]) for v in ['reference','direct'])
                if a is not None and b is not None:
                    ra,rb=(runs[v]['result'] for v in ['reference','direct'])
                    pair['same_input']=all(ra[k]==rb[k] for k in ['curve_id','planted','target','target_seed'])
                    pair['both_verified']=a['verified'] and b['verified']
                    pair['same_recovered']=a['recovered']==b['recovered']==ra['planted']
                    pair['same_counts']=all(a[stage][key]==b[stage][key] for stage,key in [
                        ('factor_base','signed_points'),('factor_base','columns'),
                        ('decomposition','targets_tried'),('decomposition','relations_found'),('linear_algebra','rank')])
                    pair['raw_cold_ratio']=cold(runs['reference'])/cold(runs['direct'])
                    pair['raw_pipeline_ratio']=a['wall_seconds']/b['wall_seconds']
                    pair['raw_counted_s_ratio']=a['s']/b['s']
                if cold(pre) is not None and cold(post) is not None:
                    pair['calibration_ratio']=cold(pre)/cold(post)
                    pair['calibration_within_bound']=.85<=pair['calibration_ratio']<=1.15
                pairs.append(pair);checkpoint()
    summary={'status':'matrix_completed_unqualified','pairs':len(pairs),'references':len(references),'qualified':None}
except Exception as e:
    summary={'status':'failed_or_capped','error':repr(e),'pairs':len(pairs),'references':len(references),'qualified':None}
finally:
    checkpoint();host['final']=snap()
    (OUT/'host.json').write_text(json.dumps(host,indent=2)+'\n')
    (OUT/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps(summary),flush=True)
if summary['status']!='matrix_completed_unqualified':raise SystemExit(1)
