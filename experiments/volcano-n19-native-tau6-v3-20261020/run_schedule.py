"""Run one part of the frozen schedule (protocol v3), one fresh pinned Sage process per run.

    sage -python run_schedule.py --part smoke|timed --lib SO --receipt-dir DIR --cpu C \
        --job-start-epoch T --deadline-min 175

v2's launcher (one `sage arm.sage` per row, affinity {C} set before exec, a
stop after a failed S0 or O1) with the Tier 1 records of the n = 83
replication's runner (koblitz-n83-closure-indexlift-rep-20261020/run_schedule.py):

* the CPU record (`scripts/host_cpu_record.py`) in `runner_start.json` and
  `runner_end.json`;
* placement: `Cpus_allowed_list` / `Cpus_allowed` of the child from
  `/proc/<pid>/status` while it runs (the arm also records its own
  `sched_getaffinity`);
* scheduling counters before and after each run: the execution CPU's
  `/proc/schedstat` line, `/proc/stat` (`ctxt`, `procs_running`,
  `procs_blocked`, the CPU's line), the child's voluntary and involuntary
  switches and minor and major faults (`getrusage`);
* the Tier 1 counters and noise gate of `scripts/isolated_bench.py` (cgroup
  cpu.stat throttling, memory events, steal on the execution CPU,
  interrupts, thermal counters, major faults);
* the library digest before and after every run, and the schedule's `role`,
  `pair`, `side` and `position` in every row.

Each run writes `rows/<part>-<serial>.json` (the arm's record) and
`logs/<part>-<serial>.{out,err}`; the arm prints that record on stdout as
`raw_b64=` with its SHA-256, which the verifier checks. Rows are appended to
`runs.jsonl` and fsynced; nothing is re-run and failed rows are kept.

Time guard (protocol design.time_guard): before each segment, if the elapsed
time since --job-start-epoch plus the larger of the segment's upper estimate
and 1.1x the longest point segment so far exceeds --deadline-min, that
segment and every later one are written as `skipped_time_guard`. A failed S0
or O1 stops the part (later rows `not_run_after_failed_gate`).
"""
import argparse
import hashlib
import json
import os
import resource
import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
sys.path.insert(0, str(REPO / 'scripts'))
import isolated_bench as ib  # noqa: E402  (Tier 1 counters and noise gate)
import host_cpu_record  # noqa: E402  (CPU model, microcode, flags)

UPPER_S = {'selftest': 900, 'O': 600, 'B': 150, 'NX': 150, 'N': 15, 'Naa': 15, 'rho': 30}
TIMEOUT_S = {'selftest': 2400, 'O': 1200, 'B': 900, 'NX': 900, 'N': 300, 'Naa': 300, 'rho': 300}
THREAD_ENV = {'OMP_NUM_THREADS': '1', 'OPENBLAS_NUM_THREADS': '1', 'MKL_NUM_THREADS': '1',
              'NUMEXPR_NUM_THREADS': '1', 'PYTHONHASHSEED': '0'}
FROZEN_FILES = ('protocol.json', 'schedule.json', 'inputs/panel.json', 'inputs/multi_systems.json', 'arm.sage',
                'native_binding.py', 'relation_digest.py', 'run_schedule.py', 'verify_receipt.py', 'stats.py',
                'native/src/lib.rs', 'native/Cargo.toml', 'native/Cargo.lock')
BASELINE_FILES = ('../volcano-ic/tau.sage', '../volcano-ic/run.sage', '../volcano-ic/ic.sage',
                  '../volcano-ic/rho-arm-20261014/rho_frob.py', '../volcano-ic/rho-arm-20261014/protocol.json',
                  '../volcano-ic/rho-arm-20261014/results/arms.jsonl',
                  '../volcano-ic/rho-arm-20261014/results/runtime-info.json')


def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for block in iter(lambda: f.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()


def read(path):
    try:
        return Path(path).read_text()
    except OSError:
        return None


def sched_counters(cpu):
    out = {'schedstat': None, 'stat_cpu': None}
    for line in (read('/proc/schedstat') or '').splitlines():
        if line.startswith('cpu%d ' % cpu):
            out['schedstat'] = [int(v) for v in line.split()[1:]]
    for line in (read('/proc/stat') or '').splitlines():
        words = line.split()
        if not words:
            continue
        if words[0] == 'cpu%d' % cpu:
            out['stat_cpu'] = [int(v) for v in words[1:]]
        elif words[0] in ('ctxt', 'procs_running', 'procs_blocked'):
            out[words[0]] = int(words[1])
    return out


def placement(pid):
    status = read('/proc/%d/status' % pid) or ''
    fields = dict(line.split(':', 1) for line in status.splitlines() if ':' in line)
    return {k: fields[k].strip() if k in fields else None for k in ('Cpus_allowed_list', 'Cpus_allowed')}


def counters(cpus, cgroup):
    try:
        return ib.counters(cpus, cgroup)
    except Exception as e:  # recorded, and the verifier fails the row's Tier 1 record
        return {'error': repr(e)}


def command(sage, run, part, lib, out):
    cmd = [sage, str(HERE / 'arm.sage'), '--arm', run['arm'], '--serial', str(run['serial']), '--lib', lib,
           '--out', out]
    if run.get('point') is not None:
        cmd += ['--point', run['point'], '--scalar', str(run['scalar']), '--rng-seed', run['rng_seed']]
    if run.get('warm'):
        cmd.append('--warm')
    return cmd


def one(run, part, args, sage, receipt, cgroup, env):
    stem = '%s-%03d' % (part, run['serial'])
    out = str(receipt / 'rows' / (stem + '.json'))
    argv = command(sage, run, part, args.lib, out)
    lib_before = sha256(args.lib)
    cpus = {args.cpu}
    before = counters(cpus, cgroup)
    sched_before = sched_counters(args.cpu)
    usage_before = resource.getrusage(resource.RUSAGE_CHILDREN)
    started_utc = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
    t0 = time.monotonic_ns()
    cpu = args.cpu
    proc = subprocess.Popen(argv, cwd=str(HERE), env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            start_new_session=True, preexec_fn=lambda: os.sched_setaffinity(0, {cpu}))
    placed = placement(proc.pid)
    timed_out = False
    try:
        so, se = proc.communicate(timeout=TIMEOUT_S[run['arm']])
    except subprocess.TimeoutExpired:
        timed_out = True
        os.killpg(proc.pid, signal.SIGKILL)
        so, se = proc.communicate()
    wall_s = (time.monotonic_ns() - t0) / 1e9
    usage_after = resource.getrusage(resource.RUSAGE_CHILDREN)
    after = counters(cpus, cgroup)
    sched_after = sched_counters(args.cpu)
    (receipt / 'logs' / (stem + '.out')).write_bytes(so)
    (receipt / 'logs' / (stem + '.err')).write_bytes(se)
    issues, contention = [], []
    if 'error' in before or 'error' in after:
        issues.append('isolated_bench counters unavailable')
    else:
        noise = ib.noise(before, after, usage_before, usage_after, 'tier1')
        issues += [x for x in noise if x.startswith('memory event')]
        contention = [x for x in noise if not x.startswith('memory event')]
    if proc.returncode != 0:
        issues.append('nonzero exit %r' % proc.returncode)
    if timed_out:
        issues.append('timeout')
    if not os.path.exists(out):
        issues.append('no row file')
    lib_after = sha256(args.lib)
    if lib_after != lib_before:
        issues.append('native library changed during the run')
    return {'part': part, 'serial': run['serial'], 'arm': run['arm'], 'point': run.get('point'),
            'role': run['role'], 'pair': run['pair'], 'side': run['side'], 'position': run['position'],
            'status': 'valid' if not issues else 'invalid', 'issues': issues, 'contention_flags': contention,
            'command': argv[1:], 'returncode': proc.returncode, 'timed_out': timed_out,
            'started_utc': started_utc, 'finished_unix_s': time.time(), 'launcher_wall_s': wall_s,
            'child_cpu_user_s': usage_after.ru_utime - usage_before.ru_utime,
            'child_cpu_system_s': usage_after.ru_stime - usage_before.ru_stime,
            'child_peak_rss_kb_cumulative': usage_after.ru_maxrss,
            'child_voluntary_switches': usage_after.ru_nvcsw - usage_before.ru_nvcsw,
            'child_involuntary_switches': usage_after.ru_nivcsw - usage_before.ru_nivcsw,
            'child_minor_faults': usage_after.ru_minflt - usage_before.ru_minflt,
            'child_major_faults': usage_after.ru_majflt - usage_before.ru_majflt,
            'placement': dict(placed, execution_cpu=args.cpu),
            'sched_before': sched_before, 'sched_after': sched_after,
            'counters_before': before, 'counters_after': after,
            'native_sha256_before': lib_before, 'native_sha256_after': lib_after,
            'row_file': 'rows/%s.json' % stem, 'stdout_file': 'logs/%s.out' % stem,
            'stderr_file': 'logs/%s.err' % stem}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--part', required=True, choices=('smoke', 'timed'))
    ap.add_argument('--lib', required=True)
    ap.add_argument('--receipt-dir', required=True, type=Path)
    ap.add_argument('--cpu', required=True, type=int)
    ap.add_argument('--job-start-epoch', required=True, type=float)
    ap.add_argument('--deadline-min', type=float, default=175)
    args = ap.parse_args()
    args.lib = os.path.abspath(args.lib)
    sched = json.load(open(HERE / 'schedule.json'))
    part = sched['parts'][args.part]
    receipt = args.receipt_dir.resolve()
    for d in ('rows', 'logs'):
        (receipt / d).mkdir(parents=True, exist_ok=False)
    sage = shutil.which('sage')
    cgroup = ib.current_cgroup()
    env = dict(os.environ)
    env.update(THREAD_ENV)
    start = {'part': args.part, 'job_start_epoch': args.job_start_epoch, 'runner_started_epoch': time.time(),
             'execution_cpu': args.cpu, 'cgroup': str(cgroup), 'sage': sage, 'deadline_min': args.deadline_min,
             'host': ib.host_probe(), 'cpu_record': host_cpu_record.record(args.cpu),
             'env_overrides': THREAD_ENV, 'native_sha256': sha256(args.lib),
             'frozen_sha256': {f: sha256(HERE / f) for f in FROZEN_FILES},
             'baseline_sha256': {f: sha256(HERE / f) for f in BASELINE_FILES},
             'isolated_bench_sha256': sha256(REPO / 'scripts' / 'isolated_bench.py'),
             'host_cpu_record_sha256': sha256(REPO / 'scripts' / 'host_cpu_record.py'),
             'upper_estimate_s': UPPER_S, 'timeout_s': TIMEOUT_S}
    (receipt / 'runner_start.json').write_text(json.dumps(start, indent=1, sort_keys=True) + '\n')
    counts, stop, guard, longest = {}, None, False, 0.0
    with open(receipt / 'runs.jsonl', 'w') as ledger:
        def write(row):
            ledger.write(json.dumps(row, sort_keys=True) + '\n')
            ledger.flush()
            os.fsync(ledger.fileno())
            counts[row['status']] = counts.get(row['status'], 0) + 1
            print(json.dumps({k: row.get(k) for k in ('part', 'serial', 'arm', 'point', 'role', 'status', 'issues',
                                                      'launcher_wall_s')}), flush=True)

        for seg in part['segments']:
            elapsed = time.time() - args.job_start_epoch
            projected = sum(UPPER_S[r['arm']] for r in seg['runs'])
            if seg['kind'] == 'point':
                projected = max(projected, 1.1 * longest)
            if stop is None and not guard and elapsed + projected > args.deadline_min * 60:
                guard = True
            seg_t0 = time.time()
            for run in seg['runs']:
                base = {'part': args.part, 'serial': run['serial'], 'arm': run['arm'], 'point': run.get('point'),
                        'role': run['role'], 'pair': run['pair'], 'side': run['side'], 'position': run['position'],
                        'segment': seg['id']}
                if stop is not None:
                    write(dict(base, status='not_run_after_failed_gate', gate=stop))
                    continue
                if guard:
                    write(dict(base, status='skipped_time_guard', elapsed_s_at_guard=elapsed))
                    continue
                row = one(run, args.part, args, sage, receipt, cgroup, env)
                row['segment'] = seg['id']
                write(row)
                if seg['kind'] == 'gate' and row['status'] != 'valid':
                    stop = '%s-%03d' % (args.part, run['serial'])
            if seg['kind'] == 'point':
                longest = max(longest, time.time() - seg_t0)
    end = {'finished_epoch': time.time(), 'counts': counts, 'guard_tripped': guard, 'stopped_after_gate': stop,
           'cpu_record': host_cpu_record.record(args.cpu), 'native_sha256_after': sha256(args.lib),
           'frozen_sha256_after': {f: sha256(HERE / f) for f in FROZEN_FILES}}
    (receipt / 'runner_end.json').write_text(json.dumps(end, indent=1, sort_keys=True) + '\n')
    print(json.dumps({k: end[k] for k in ('counts', 'guard_tripped', 'stopped_after_gate')}), flush=True)
    sys.exit(0 if stop is None and not guard else 4)


if __name__ == '__main__':
    main()
