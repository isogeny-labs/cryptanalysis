"""Run the frozen schedule, one fresh Sage process per row, on one pinned CPU.

    sage -python run_schedule.py --lib SO --receipt-dir DIR --cpu C \
        --job-start-epoch T --deadline-min 300

Each row is `sage arm.sage --arm ... --out DIR/rows/<row>.json`, launched with
its CPU affinity set to {C}. The launcher records its own wall time for the
whole process (Sage start-up and source loading included), the exit code and
the stdout / stderr. A segment is skipped (rows `skipped_time_guard`) if the
elapsed job time plus its upper estimate would pass the deadline. A failed
S0 or O1 row stops the schedule before any timed segment.
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
UPPER_S = {'selftest': 300, 'O': 600, 'B': 900, 'NX': 900, 'N': 300, 'Naa': 300, 'rho': 300}
TIMEOUT_S = {'selftest': 900, 'O': 1200, 'B': 1800, 'NX': 1800, 'N': 600, 'Naa': 600, 'rho': 600}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--lib', required=True)
    ap.add_argument('--receipt-dir', required=True)
    ap.add_argument('--cpu', type=int, required=True)
    ap.add_argument('--job-start-epoch', type=float, required=True)
    ap.add_argument('--deadline-min', type=float, default=300)
    a = ap.parse_args()
    sched = json.load(open(os.path.join(HERE, 'schedule.json')))
    rows_dir = os.path.join(a.receipt_dir, 'rows')
    logs_dir = os.path.join(a.receipt_dir, 'logs')
    os.makedirs(rows_dir, exist_ok=True)
    os.makedirs(logs_dir, exist_ok=True)
    sage = shutil.which('sage')
    runs = open(os.path.join(a.receipt_dir, 'runs.jsonl'), 'w')
    stop = None
    for seg in sched['segments']:
        est = sum(UPPER_S[r['arm']] for r in seg['rows'])
        elapsed = time.time() - a.job_start_epoch
        for r in seg['rows']:
            rec = {'segment': seg['id'], **r}
            if stop is not None:
                rec['status'] = 'not_run_after_failed_gate:' + stop
            elif elapsed + est > a.deadline_min * 60:
                rec['status'] = 'skipped_time_guard'
            else:
                out = os.path.join(rows_dir, r['row'] + '.json')
                cmd = [sage, os.path.join(HERE, 'arm.sage'), '--arm', r['arm'], '--lib', a.lib, '--out', out]
                if 'point' in r:
                    cmd += ['--point', r['point'], '--scalar', str(r['scalar']), '--rng-seed', r['rng_seed']]
                cpu = a.cpu
                t0 = time.perf_counter()
                rec['started_utc'] = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
                try:
                    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                       timeout=TIMEOUT_S[r['arm']], preexec_fn=lambda: os.sched_setaffinity(0, {cpu}))
                    rec['exit'] = p.returncode
                    so, se = p.stdout, p.stderr
                except subprocess.TimeoutExpired as e:
                    rec['exit'] = 'timeout'
                    so, se = e.stdout or b'', e.stderr or b''
                rec['launcher_wall_s'] = time.perf_counter() - t0
                open(os.path.join(logs_dir, r['row'] + '.out'), 'wb').write(so)
                open(os.path.join(logs_dir, r['row'] + '.err'), 'wb').write(se)
                rec['status'] = 'ran'
                if os.path.exists(out):
                    rec['result'] = json.load(open(out))
                if seg['id'] in ('S0', 'O1') and (rec['exit'] != 0 or not rec.get('result', {}).get('correct')):
                    stop = r['row']
            runs.write(json.dumps(rec) + '\n')
            runs.flush()
            print(json.dumps({k: rec.get(k) for k in ('row', 'status', 'exit', 'launcher_wall_s')}), flush=True)
    runs.close()
    sys.exit(0 if stop is None else 4)


if __name__ == '__main__':
    main()
