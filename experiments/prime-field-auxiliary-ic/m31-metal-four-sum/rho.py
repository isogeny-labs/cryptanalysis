#!/usr/bin/env python3
"""Matched archived C++ rho distance control for CONFIRM2."""
import hashlib
import json
import os
from pathlib import Path
import resource
import subprocess
import tempfile
import time

ROOT=Path(__file__).resolve().parents[3]
HERE=Path(__file__).resolve().parent
PATHS=['common.hpp','compare_rho.cpp']
HASHES=['7f54ac2b36ebb0bf569a7a5ae2a376706e336582a74e822d9e04c3f7fab3414e',
        '430b7f5e022314f3a2f2fabac66bd0a6a1deee93cd91395520a48ad831a47de2']

def usage():
    x=resource.getrusage(resource.RUSAGE_CHILDREN)
    return x.ru_utime+x.ru_stime

def main():
    if subprocess.check_output(['git','status','--porcelain'],cwd=ROOT).strip():
        raise SystemExit('freeze checkout before rho run')
    manifest=json.loads((HERE/'CONFIRM2_MANIFEST.json').read_text())
    records=[]
    out=HERE/'RHO_RAW.jsonl'
    if out.exists(): raise SystemExit('rho raw output already exists')
    with tempfile.TemporaryDirectory(prefix='m31-rho-matched-') as tmp:
        tmp=Path(tmp)
        for name,expected in zip(PATHS,HASHES):
            source=subprocess.check_output(['git','show',f'HEAD:experiments/prime-field-auxiliary-ic/snapshot/comparison/{name}'],cwd=ROOT)
            assert hashlib.sha256(source).hexdigest()==expected
            (tmp/name).write_bytes(source)
        binary=tmp/'compare_rho'
        subprocess.run(['c++','-std=c++17','-O3','-DFIELD_BITS=31',str(tmp/'compare_rho.cpp'),'-o',str(binary)],check=True)
        binary_sha=hashlib.sha256(binary.read_bytes()).hexdigest()
        (HERE/'RHO_MANIFEST.json').write_text(json.dumps({'schema':'m31-metal-rho-manifest/v1',
            'source_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
            'binary_sha256':binary_sha,'source_sha256':dict(zip(PATHS,HASHES)),
            'confirm2_commit':manifest['commit'],'targets':manifest['targets'],'seeds':manifest['seeds']},indent=2)+'\n')
        with out.open('x') as stream:
            for t,s in [(t,s) for t in range(5) for s in range(3)]:
                qx,qy=manifest['targets'][t]; seed=manifest['seeds'][s]
                before=usage(); start=time.perf_counter_ns()
                with tempfile.TemporaryDirectory(prefix=f't{t}-s{s}-',dir=tmp) as wd:
                    wd=Path(wd)
                    (wd/'public.txt').write_text(f'2147483647 2147505293 2 14\n1 814455902 {qx} {qy}\n0\n')
                    try:
                        proc=subprocess.run([str(binary),str(seed)],cwd=wd,capture_output=True,text=True,timeout=12)
                        stdout,stderr,code,timeout=proc.stdout,proc.stderr,proc.returncode,False
                    except subprocess.TimeoutExpired as exc:
                        stdout,stderr,code,timeout=str(exc.stdout),str(exc.stderr),None,True
                    metrics=json.loads((wd/'metrics.json').read_text()) if (wd/'metrics.json').exists() else None
                record={'target':t,'seed':seed,'Q':[qx,qy],'returncode':code,'timeout':timeout,
                        'stdout':stdout.strip(),'stderr':stderr.strip(),'metrics':metrics,
                        'wall_ns':time.perf_counter_ns()-start,'cpu_ns':round((usage()-before)*1e9)}
                records.append(record)
                stream.write(json.dumps(record,sort_keys=True)+'\n'); stream.flush(); os.fsync(stream.fileno())
    print(json.dumps({'arms':len(records),'completed':sum(x['returncode']==0 for x in records),
                      'binary_sha256':binary_sha}))

if __name__=='__main__': main()
