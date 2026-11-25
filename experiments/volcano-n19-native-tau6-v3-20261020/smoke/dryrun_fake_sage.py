"""Dry run of run_schedule.py + verify_receipt.py with a stand-in `sage` (no Sage; mechanics only).

    python3 smoke/dryrun_fake_sage.py --lib PATH/libtau6native.so --out smoke/dryrun_fake_sage.json

A stand-in `sage` executable on PATH answers each `sage arm.sage ...` the
runner launches with a synthetic record (tests/test_verify_receipt.raw_for),
with this process's real affinity and the library's real SHA-256, in the
arm's stdout format. The real runner then launches every run of a part as a
pinned child and records placement, schedstat, rusage and the isolated_bench
counters on this VM, and the real verifier audits the receipt. This checks
the runner, the record formats and the verifier together; the arms
themselves are exercised only by the Sage smoke job.
"""
import argparse
import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
V3 = os.path.dirname(HERE)

FAKE = r'''#!/usr/bin/env python3
import base64, hashlib, json, os, sys
sys.path.insert(0, %(tests)r)
sys.path.insert(0, %(v3)r)
import test_verify_receipt as T
a = sys.argv[2:]
opt = lambda k: a[a.index(k) + 1] if k in a else None
serial = int(opt('--serial'))
part = %(part)r
run = next(r for s in T.SCHED['parts'][part]['segments'] for r in s['runs'] if r['serial'] == serial)
assert run['arm'] == opt('--arm')
pts = sorted({r['point'] for s in T.SCHED['parts'][part]['segments'] for r in s['runs'] if r.get('point')})
raw = T.raw_for(run, {p: 1 + 0.1 * i for i, p in enumerate(pts)})
raw['affinity'] = sorted(os.sched_getaffinity(0))
raw['native_sha256'] = hashlib.sha256(open(opt('--lib'), 'rb').read()).hexdigest()
b = json.dumps(raw, sort_keys=True, separators=(',', ':')).encode()
open(opt('--out'), 'wb').write(b + b'\n')
print('raw_b64=' + base64.b64encode(b).decode())
print('raw_result_sha256=%%s serial=%%d arm=%%s point=%%s correct=1' %% (hashlib.sha256(b).hexdigest(), serial,
      run['arm'], run.get('point')))
'''


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--lib', required=True)
    ap.add_argument('--out', required=True)
    args = ap.parse_args()
    tmp = tempfile.mkdtemp()
    res = {'kind': 'dry run with a stand-in sage (mechanics of runner + verifier only; no Sage, no timing)'}
    try:
        for part in ('smoke',):
            bindir = os.path.join(tmp, 'bin-' + part)
            os.makedirs(bindir)
            fake = os.path.join(bindir, 'sage')
            open(fake, 'w').write(FAKE % {'tests': os.path.join(V3, 'tests'), 'v3': V3, 'part': part})
            os.chmod(fake, os.stat(fake).st_mode | stat.S_IEXEC)
            env = dict(os.environ, PATH=bindir + os.pathsep + os.environ['PATH'])
            rd = os.path.join(tmp, part)
            cpu = min(os.sched_getaffinity(0))
            p = subprocess.run([sys.executable, os.path.join(V3, 'run_schedule.py'), '--part', part, '--lib', args.lib,
                                '--receipt-dir', rd, '--cpu', str(cpu), '--job-start-epoch', str(time.time()),
                                '--deadline-min', '30'], env=env, capture_output=True, text=True)
            v = subprocess.run([sys.executable, os.path.join(V3, 'verify_receipt.py'), '--part', part, rd],
                               capture_output=True, text=True)
            corr = json.load(open(os.path.join(rd, 'correctness.json')))
            rows = [json.loads(l) for l in open(os.path.join(rd, 'runs.jsonl'))]
            res[part] = {'runner_exit': p.returncode, 'runner_stderr_tail': p.stderr.splitlines()[-5:],
                         'verifier_exit': v.returncode, 'gates': corr['gates'], 'gate_names': corr['gate_names'],
                         'smoke_gate_passed': corr['smoke_gate_passed'], 'rows': len(rows),
                         'example_row_isolation_fields': sorted(rows[-1])}
    finally:
        shutil.rmtree(tmp)
    # This VM has no /proc/schedstat, so tier1_counters_recorded is expected to be the one false gate here.
    res['proc_schedstat_present'] = os.path.exists('/proc/schedstat')
    allowed = set() if res['proc_schedstat_present'] else {'tier1_counters_recorded'}
    res['ok'] = all(res[p]['runner_exit'] == 0 and set(res[p]['gate_names']['not_true']) <= allowed and
                    not res[p]['gate_names']['unknown'] and not res[p]['gate_names']['missing'] for p in ('smoke',))
    json.dump(res, open(args.out, 'w'), indent=1, sort_keys=True)
    print(json.dumps(res, indent=1, sort_keys=True)[:3000])
    if not res['ok']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
