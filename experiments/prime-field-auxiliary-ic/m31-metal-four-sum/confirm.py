#!/usr/bin/env python3
"""Frozen same-target cold full-solve CPU/Metal panel; compilation precedes timing."""
import hashlib
import json
import os
from pathlib import Path
import platform
import random
import resource
import statistics
import subprocess
import tempfile
import time

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
TARGETS = [(1767503692,244402461),(686106551,2137700595),
           (949616523,2050168716),(1568678311,615355077),
           (2146214436,1536824028)]
SEEDS = [3896374591561183853,8665303581124560846,5306259987485486766]
ORDER_SEED = 4571280975418445854
SOURCES = [HERE/'full.rs',HERE/'gpu_ffi.swift',HERE/'screen.metal',
           ROOT/'crates/prime-field-auxiliary-ic/src/solve.rs',
           ROOT/'crates/prime-field-auxiliary-ic/src/pair_index.rs']

def run(args, **kw):
    return subprocess.run([str(x) for x in args], check=True, text=True,
                          capture_output=True, **kw)

def usage():
    r=resource.getrusage(resource.RUSAGE_CHILDREN)
    return r.ru_utime+r.ru_stime

def main():
    if run(['git','status','--porcelain'],cwd=ROOT).stdout.strip():
        raise SystemExit('source checkout must be clean before the frozen run')
    commit=run(['git','rev-parse','HEAD'],cwd=ROOT).stdout.strip()
    manifest={'schema':'m31-metal-confirm-manifest/v1','commit':commit,
              'host':platform.platform(),'python':platform.python_version(),
              'rustc':run(['rustc','--version']).stdout.strip(),
              'swiftc':run(['swiftc','--version']).stdout.strip(),
              'source_sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in SOURCES},
              'targets':TARGETS,'seeds':SEEDS,'order_seed':ORDER_SEED,
              'master_seed_hex':'d82249cb5818e02991b6f77d75810526'}
    blocks=[(t,s) for t in range(5) for s in range(3)]
    random.Random(ORDER_SEED).shuffle(blocks)
    schedule=[{'target':t,'seed':s,'arms':(['cpu','metal'] if i%2==0 else ['metal','cpu'])}
              for i,(t,s) in enumerate(blocks)]
    manifest['schedule']=schedule
    out=HERE/'CONFIRM_RAW.jsonl'
    if out.exists() or (HERE/'CONFIRM_MANIFEST.json').exists():
        raise SystemExit('confirmation output exists; do not overwrite')
    (HERE/'CONFIRM_MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n')
    with tempfile.TemporaryDirectory(prefix='m31-metal-confirm-') as d:
        d=Path(d)
        lib=d/'libprime_field_auxiliary_ic.rlib'
        dylib=d/'libm31metal.dylib'
        binary=d/'m31-metal-full'
        run(['rustc','--edition','2021','--crate-type','lib','--crate-name','prime_field_auxiliary_ic','-O',
             ROOT/'crates/prime-field-auxiliary-ic/src/lib.rs','-o',lib],cwd=ROOT)
        run(['swiftc','-O','-emit-library',HERE/'gpu_ffi.swift','-o',dylib],cwd=ROOT)
        run(['rustc','--edition','2021','-O',HERE/'full.rs','--extern',f'prime_field_auxiliary_ic={lib}',
             '-L',f'native={d}','-C',f'link-arg=-Wl,-rpath,{d}','-o',binary],cwd=ROOT)
        with out.open('x') as stream:
            for block in schedule:
                t,s=block['target'],block['seed']
                qx,qy=TARGETS[t]
                for arm in block['arms']:
                    cpu0=usage(); wall0=time.perf_counter_ns()
                    try:
                        proc=subprocess.run([str(binary),arm,str(qx),str(qy),str(s)],cwd=ROOT,
                                            capture_output=True,text=True,timeout=12)
                        record={'returncode':proc.returncode,'stdout':proc.stdout.strip(),
                                'stderr':proc.stderr.strip(),'timeout':False}
                    except subprocess.TimeoutExpired as exc:
                        record={'returncode':None,'stdout':str(exc.stdout),'stderr':str(exc.stderr),'timeout':True}
                    record.update({'target':t,'seed':s,'mode':arm,'Q':[qx,qy],
                                   'wall_ns':time.perf_counter_ns()-wall0,
                                   'cpu_ns':round((usage()-cpu0)*1e9)})
                    stream.write(json.dumps(record,sort_keys=True)+'\n')
                    stream.flush(); os.fsync(stream.fileno())
    records=[json.loads(line) for line in out.read_text().splitlines()]
    pairs=[]
    for t,s in blocks:
        arms={r['mode']:r for r in records if r['target']==t and r['seed']==s}
        if len(arms)!=2 or any(r['returncode']!=0 for r in arms.values()):
            continue
        a,b=(json.loads(arms[m]['stdout']) for m in ['cpu','metal'])
        if any(a[k]!=b[k] for k in ['scalar','certificate_digest','queries','relations','rank']):
            continue
        pairs.append({'target':t,'seed':s,'wall_ratio':arms['cpu']['wall_ns']/arms['metal']['wall_ns'],
                      'cpu_ratio':arms['cpu']['cpu_ns']/arms['metal']['cpu_ns']})
    summary={'schema':'m31-metal-confirm-summary/v1','arms':len(records),'valid_pairs':len(pairs),
             'median_wall_ratio':statistics.median(x['wall_ratio'] for x in pairs) if pairs else None,
             'median_cpu_ratio':statistics.median(x['cpu_ratio'] for x in pairs) if pairs else None,
             'wall_wins':sum(x['wall_ratio']>1 for x in pairs),
             'cpu_wins':sum(x['cpu_ratio']>1 for x in pairs),'pairs':pairs}
    (HERE/'CONFIRM_SUMMARY.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps(summary))

if __name__=='__main__': main()
