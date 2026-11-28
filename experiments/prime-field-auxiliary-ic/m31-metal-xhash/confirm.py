#!/usr/bin/env python3
"""Frozen same-target M31 Metal 20-versus-xhash22 bitmap panel."""
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
METAL = HERE.parent/'m31-metal-four-sum'
TARGETS = [(1767503692,244402461),(686106551,2137700595),
           (949616523,2050168716),(1568678311,615355077),
           (2146214436,1536824028)]
SEEDS = [4454329044419911484,2812151391946316817,5598324525605962919]
ORDER_SEED = 7522161479198906941
SOURCES = [METAL/'full.rs',METAL/'gpu_ffi.swift',METAL/'screen.metal',
           HERE/'confirm.py',HERE/'verify_confirm.py',HERE/'CONFIRM_PROTOCOL.md',
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
    manifest={'schema':'m31-metal-xhash22-confirm-manifest/v1','commit':commit,
              'host':platform.platform(),'python':platform.python_version(),
              'rustc':run(['rustc','--version']).stdout.strip(),
              'swiftc':run(['swiftc','--version']).stdout.strip(),
              'source_sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in SOURCES},
              'targets':TARGETS,'seeds':SEEDS,'order_seed':ORDER_SEED,
              'master_seed_hex':'965f4d402259576f911490040e630052'}
    blocks=[(t,s) for t in range(5) for s in range(3)]
    random.Random(ORDER_SEED).shuffle(blocks)
    schedule=[{'target':t,'seed':s,'arms':(['20','xhash22'] if i%2==0 else ['xhash22','20'])}
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
        run(['swiftc','-O','-emit-library',METAL/'gpu_ffi.swift','-o',dylib],cwd=ROOT)
        run(['rustc','--edition','2021','-O',METAL/'full.rs','--extern',f'prime_field_auxiliary_ic={lib}',
             '-L',f'native={d}','-C',f'link-arg=-Wl,-rpath,{d}','-o',binary],cwd=ROOT)
        manifest['binary_sha256']=hashlib.sha256(binary.read_bytes()).hexdigest()
        (HERE/'CONFIRM_MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n')
        admission=[]
        qx,qy=TARGETS[0]
        for screen_mode in (0,2):
            env=os.environ.copy()
            env['M31_AUDIT_FLAGS']='1'
            if screen_mode==2:
                env['M31_AUDIT_EXACT_X']='1'
            proc=subprocess.run([str(binary),'metal',str(qx),str(qy),
                                 '2911332506172719186','22',str(screen_mode)],
                                cwd=ROOT,env=env,capture_output=True,text=True,timeout=30)
            admission.append({'screen_mode':screen_mode,'returncode':proc.returncode,
                              'stdout':proc.stdout.strip(),'stderr':proc.stderr.strip()})
        (HERE/'CONFIRM_ADMISSION.jsonl').write_text(''.join(json.dumps(x,sort_keys=True)+'\n' for x in admission))
        if any(x['returncode']!=0 for x in admission):
            raise SystemExit('exact-x admission process failed; timed panel not started')
        before,after=(json.loads(x['stdout']) for x in admission)
        if any(before[k]!=after[k] for k in ['scalar','certificate_digest','queries','relations','rank']):
            raise SystemExit('exact-x admission certificate mismatch; timed panel not started')
        with out.open('x') as stream:
            for block in schedule:
                t,s=block['target'],block['seed']
                qx,qy=TARGETS[t]
                for arm in block['arms']:
                    bits=20 if arm=='20' else 22
                    coarse=0 if arm=='20' else 2
                    cpu0=usage(); wall0=time.perf_counter_ns()
                    try:
                        proc=subprocess.run([str(binary),'metal',str(qx),str(qy),str(SEEDS[s]),str(bits),str(coarse)],cwd=ROOT,
                                            capture_output=True,text=True,timeout=12)
                        record={'returncode':proc.returncode,'stdout':proc.stdout.strip(),
                                'stderr':proc.stderr.strip(),'timeout':False}
                    except subprocess.TimeoutExpired as exc:
                        record={'returncode':None,'stdout':str(exc.stdout),'stderr':str(exc.stderr),'timeout':True}
                    record.update({'target':t,'seed_index':s,'seed':SEEDS[s],'arm':arm,
                                   'bitmap_bits':bits,'use_coarse':coarse,'Q':[qx,qy],
                                   'wall_ns':time.perf_counter_ns()-wall0,
                                   'cpu_ns':round((usage()-cpu0)*1e9)})
                    stream.write(json.dumps(record,sort_keys=True)+'\n')
                    stream.flush(); os.fsync(stream.fileno())
    records=[json.loads(line) for line in out.read_text().splitlines()]
    pairs=[]
    for t,s in blocks:
        arms={r['arm']:r for r in records if r['target']==t and r['seed_index']==s}
        if len(arms)!=2 or any(r['returncode']!=0 for r in arms.values()):
            continue
        a,b=(json.loads(arms[m]['stdout']) for m in ['20','xhash22'])
        if any(a[k]!=b[k] for k in ['scalar','certificate_digest','queries','relations','rank']):
            continue
        pairs.append({'target':t,'seed_index':s,'wall_ratio':arms['20']['wall_ns']/arms['xhash22']['wall_ns'],
                      'cpu_ratio':arms['20']['cpu_ns']/arms['xhash22']['cpu_ns'],
                      'positive_ratio':a['positive_flags']/b['positive_flags']})
    summary={'schema':'m31-metal-xhash22-confirm-summary/v1','arms':len(records),'valid_pairs':len(pairs),
             'median_wall_ratio':statistics.median(x['wall_ratio'] for x in pairs) if pairs else None,
             'median_cpu_ratio':statistics.median(x['cpu_ratio'] for x in pairs) if pairs else None,
             'wall_wins':sum(x['wall_ratio']>1 for x in pairs),
             'cpu_wins':sum(x['cpu_ratio']>1 for x in pairs),'pairs':pairs}
    (HERE/'CONFIRM_SUMMARY.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps(summary))

if __name__=='__main__': main()
