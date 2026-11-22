"""Local dry run of run_schedule.py + the real tau6dlp + verify_receipt.py, with a stand-in `sage`
(smoke/fake_sage.py: the pure-Python model). Mechanics and integration only; NOT Sage, NOT timing.

    python3 smoke/dryrun_model_sage.py --v3lib V3SO --lib LOOPSO --bin TAU6DLP --out smoke/dryrun_model_sage.json

The real launcher runs the smoke part: the binary arms (N2, N2aa, O2, S0b) for real, every
other arm through the stand-in. The real verifier then audits the receipt. On this VM
/proc/schedstat is absent, so tier1_counters_recorded is the one gate allowed to be false.
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
EXP = os.path.dirname(HERE)


def main():
    ap = argparse.ArgumentParser()
    for k in ('--v3lib', '--lib', '--bin', '--out'):
        ap.add_argument(k, required=True)
    a = ap.parse_args()
    tmp = tempfile.mkdtemp()
    res = {'kind': 'dry run: real launcher, real tau6dlp, real verifier, stand-in sage (pure-Python model); '
                   'mechanics only, no Sage, no timing'}
    try:
        bindir = os.path.join(tmp, 'bin')
        os.makedirs(bindir)
        fake = os.path.join(bindir, 'sage')
        shutil.copy(os.path.join(HERE, 'fake_sage.py'), fake)
        os.chmod(fake, os.stat(fake).st_mode | stat.S_IEXEC)
        env = dict(os.environ, PATH=bindir + os.pathsep + os.environ['PATH'], N19_EXP=EXP)
        rd = os.path.join(tmp, 'smoke')
        cpu = min(os.sched_getaffinity(0))
        p = subprocess.run([sys.executable, os.path.join(EXP, 'run_schedule.py'), '--part', 'smoke', '--v3lib',
                            a.v3lib, '--lib', a.lib, '--bin', a.bin, '--receipt-dir', rd, '--cpu', str(cpu),
                            '--job-start-epoch', str(time.time()), '--deadline-min', '30'], env=env,
                           capture_output=True, text=True)
        v = subprocess.run([sys.executable, os.path.join(EXP, 'verify_receipt.py'), '--part', 'smoke', rd],
                           capture_output=True, text=True)
        corr = json.load(open(os.path.join(rd, 'correctness.json')))
        rows = [json.loads(l) for l in open(os.path.join(rd, 'runs.jsonl'))]
        res.update({'runner_exit': p.returncode, 'runner_stdout_tail': p.stdout.splitlines()[-4:],
                    'runner_stderr_tail': p.stderr.splitlines()[-5:], 'verifier_exit': v.returncode,
                    'gates': corr['gates'], 'gate_names': corr['gate_names'], 'detail_s0b': corr['detail'].get('s0b'),
                    'invalid_rows': corr['detail'].get('invalid_rows'), 'problems': corr['detail'].get('problems'),
                    'rows': len(rows), 'statuses': sorted({r['status'] for r in rows}),
                    'binary_rows_launcher_wall_s': [round(r.get('launcher_wall_s', -1), 4) for r in rows
                                                    if r['arm'] in ('N2', 'N2aa')]})
    finally:
        shutil.rmtree(tmp)
    res['proc_schedstat_present'] = os.path.exists('/proc/schedstat')
    allowed = set() if res['proc_schedstat_present'] else {'tier1_counters_recorded'}
    res['ok'] = res['runner_exit'] == 0 and set(res['gate_names']['not_true']) <= allowed and \
        not res['gate_names']['unknown'] and not res['gate_names']['missing']
    json.dump(res, open(a.out, 'w'), indent=1, sort_keys=True)
    print(json.dumps({k: res[k] for k in ('ok', 'runner_exit', 'gate_names', 'rows', 'statuses')}, indent=1))
    if not res['ok']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
