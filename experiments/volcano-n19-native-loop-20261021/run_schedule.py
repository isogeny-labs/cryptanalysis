"""Run one part of the frozen schedule of volcano-n19-native-loop-20261021, one fresh pinned
process per run.

    sage -python run_schedule.py --part smoke|timed --v3lib SO --lib SO --bin EXE --receipt-dir DIR \
        --cpu C --job-start-epoch T --deadline-min 175

The launcher of ../volcano-n19-native-tau6-v3-20261020/run_schedule.py (affinity {C} set
before exec, a stop after a failed gate, the Tier 1 records below), with the arms of this
protocol:

* B, N, rho, O (baseline side): `sage ../volcano-n19-native-tau6-v3-20261020/arm.sage` with
  the v3 library built from v3's own native/ (arm N is the current n = 19 row, unchanged);
* selftest (S0): the same v3 arm on libtau6loop.so (its tau6_* solve is the v3 source);
* N2, N2aa, O2, S0b (candidate side): the tau6dlp binary, no Sage process;
* N2X (planted): `sage arm_n2x.sage` with both libraries.

S0b reads the S0 row's systems (written to `s0_systems.txt` from that row, before S0b runs).
Records per run (as v3):

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

UPPER_S = {'selftest': 900, 'S0b': 30, 'O': 600, 'O2': 30, 'B': 150, 'N': 15, 'N2': 5, 'N2aa': 5, 'N2X': 30,
           'rho': 30}
TIMEOUT_S = {'selftest': 2400, 'S0b': 300, 'O': 1200, 'O2': 300, 'B': 900, 'N': 300, 'N2': 120, 'N2aa': 120,
             'N2X': 600, 'rho': 300}
V3 = '../volcano-n19-native-tau6-v3-20261020'
ARCHIVED = '../volcano-ic/rho-arm-20261014/protocol.json'
THREAD_ENV = {'OMP_NUM_THREADS': '1', 'OPENBLAS_NUM_THREADS': '1', 'MKL_NUM_THREADS': '1',
              'NUMEXPR_NUM_THREADS': '1', 'PYTHONHASHSEED': '0'}
FROZEN_FILES = ('protocol.json', 'schedule.json', 'inputs/panel.json', 'arm_n2x.sage', 'n2x_compare.py',
                'run_schedule.py', 'verify_receipt.py', 'stats.py', 'make_schedule.py', 'make_panel.py',
                'native/Cargo.toml', 'native/Cargo.lock', 'native/src/lib.rs', 'native/src/curve.rs',
                'native/src/dlp.rs', 'native/src/ffi.rs', 'native/src/json.rs', 'native/src/pyrand.rs',
                'native/src/util.rs', 'native/src/testvec.rs', 'native/src/bin/tau6dlp.rs')
BASELINE_FILES = (V3 + '/arm.sage', V3 + '/native_binding.py', V3 + '/relation_digest.py',
                  V3 + '/inputs/multi_systems.json', V3 + '/native/src/lib.rs', V3 + '/native/Cargo.toml',
                  V3 + '/native/Cargo.lock', V3 + '/run_github_39387473809/timed/panel/result.json',
                  '../volcano-ic/tau.sage', '../volcano-ic/run.sage', '../volcano-ic/ic.sage',
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


def command(sage, run, part, args, out, receipt):
    arm = run['arm']
    if arm in ('N2', 'N2aa', 'O2', 'S0b'):
        cmd = [args.bin, '--arm', arm, '--serial', str(run['serial'])]
        if arm == 'O2':
            ap = json.load(open(HERE / ARCHIVED))
            cmd += ['--scalars', ','.join(str(int(x)) for x in ap['scalars']),
                    '--seed-format', ap['arms']['tau6']['rng_seed']]
        if arm == 'S0b':
            cmd += ['--systems', str(receipt / 's0_systems.txt')]
        cmd += ['--out', out]
    elif arm == 'N2X':
        cmd = [sage, str(HERE / 'arm_n2x.sage'), '--arm', arm, '--serial', str(run['serial']), '--lib', args.lib,
               '--v3lib', args.v3lib, '--out', out]
    else:
        lib = args.lib if arm == 'selftest' else args.v3lib
        cmd = [sage, str((HERE / V3 / 'arm.sage').resolve()), '--arm', arm, '--serial', str(run['serial']),
               '--lib', lib, '--out', out]
    if run.get('point') is not None:
        cmd += ['--point', run['point'], '--scalar', str(run['scalar']), '--rng-seed', run['rng_seed']]
    if run.get('warm'):
        cmd.append('--warm')
    return cmd


def s0_systems(receipt, part):
    """The S0 row's systems as 'xR j' lines (S0b's input); the verifier recomputes this file."""
    sched = json.load(open(HERE / 'schedule.json'))['parts'][part]
    s0 = next(r for seg in sched['segments'] for r in seg['runs'] if r['arm'] == 'selftest')
    row = json.load(open(receipt / 'rows' / ('%s-%03d.json' % (part, s0['serial']))))
    text = ''.join('%d %d\n' % (int(d['xR']), int(d['j'])) for d in row['detail'])
    (receipt / 's0_systems.txt').write_text(text)


def artifacts(args):
    return {'v3lib': sha256(args.v3lib), 'lib': sha256(args.lib), 'bin': sha256(args.bin)}


def one(run, part, args, sage, receipt, cgroup, env):
    stem = '%s-%03d' % (part, run['serial'])
    out = str(receipt / 'rows' / (stem + '.json'))
    argv = command(sage, run, part, args, out, receipt)
    lib_before = artifacts(args)
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
    lib_after = artifacts(args)
    if lib_after != lib_before:
        issues.append('a native artifact changed during the run')
    return {'part': part, 'serial': run['serial'], 'arm': run['arm'], 'point': run.get('point'),
            'role': run['role'], 'pair': run['pair'], 'side': run['side'], 'position': run['position'],
            'status': 'valid' if not issues else 'invalid', 'issues': issues, 'contention_flags': contention,
            'command': argv, 'returncode': proc.returncode, 'timed_out': timed_out,
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
    ap.add_argument('--lib', required=True, help='libtau6loop.so (this crate)')
    ap.add_argument('--v3lib', required=True, help='libtau6native.so built from the v3 native/ (baseline N)')
    ap.add_argument('--bin', required=True, help='tau6dlp (this crate; arm N2)')
    ap.add_argument('--receipt-dir', required=True, type=Path)
    ap.add_argument('--cpu', required=True, type=int)
    ap.add_argument('--job-start-epoch', required=True, type=float)
    ap.add_argument('--deadline-min', type=float, default=175)
    args = ap.parse_args()
    args.lib, args.v3lib, args.bin = (os.path.abspath(x) for x in (args.lib, args.v3lib, args.bin))
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
             'env_overrides': THREAD_ENV, 'native_sha256': artifacts(args),
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
                if run['arm'] == 'S0b':
                    try:
                        s0_systems(receipt, args.part)
                    except Exception as e:  # no S0 row: S0b fails and stops the part
                        (receipt / 's0_systems.txt').write_text('')
                        print(json.dumps({'s0_systems_error': repr(e)}), flush=True)
                row = one(run, args.part, args, sage, receipt, cgroup, env)
                row['segment'] = seg['id']
                write(row)
                if seg['kind'] == 'gate' and row['status'] != 'valid':
                    stop = '%s-%03d' % (args.part, run['serial'])
            if seg['kind'] == 'point':
                longest = max(longest, time.time() - seg_t0)
    end = {'finished_epoch': time.time(), 'counts': counts, 'guard_tripped': guard, 'stopped_after_gate': stop,
           'cpu_record': host_cpu_record.record(args.cpu), 'native_sha256_after': artifacts(args),
           'frozen_sha256_after': {f: sha256(HERE / f) for f in FROZEN_FILES}}
    (receipt / 'runner_end.json').write_text(json.dumps(end, indent=1, sort_keys=True) + '\n')
    print(json.dumps({k: end[k] for k in ('counts', 'guard_tripped', 'stopped_after_gate')}), flush=True)
    sys.exit(0 if stop is None and not guard else 4)


if __name__ == '__main__':
    main()
