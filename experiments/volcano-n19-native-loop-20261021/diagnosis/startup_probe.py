"""Untimed diagnostic: Sage process start-up on the runner (no claim, no gate).

    sage -python startup_probe.py --cpu C --reps 5 --lib SO --out FILE

Launches, pinned to CPU C, REPS times each: `sage -c pass`, `sage -python -c pass`,
`sage -python -c "import sage.all"`, and `sage diagnosis/profile_n.sage --mode load` (Sage plus
the v3 arm's loads: run.sage, ic.sage, tau.sage, rho_frob, the binding). Records the launcher
wall and the child's user + system CPU (getrusage RUSAGE_CHILDREN deltas) per launch.
"""
import argparse
import json
import os
import resource
import shutil
import subprocess
import time

HERE = os.path.dirname(os.path.abspath(__file__))


def launch(argv, cpu):
    u0 = resource.getrusage(resource.RUSAGE_CHILDREN)
    t0 = time.monotonic_ns()
    p = subprocess.run(argv, cwd=HERE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                       preexec_fn=lambda: os.sched_setaffinity(0, {cpu}))
    wall = (time.monotonic_ns() - t0) / 1e9
    u1 = resource.getrusage(resource.RUSAGE_CHILDREN)
    return {'returncode': p.returncode, 'wall_s': wall,
            'child_cpu_s': (u1.ru_utime - u0.ru_utime) + (u1.ru_stime - u0.ru_stime),
            'child_user_s': u1.ru_utime - u0.ru_utime, 'child_sys_s': u1.ru_stime - u0.ru_stime,
            'stderr_tail': p.stderr.decode(errors='replace')[-400:]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--cpu', type=int, required=True)
    ap.add_argument('--reps', type=int, default=5)
    ap.add_argument('--lib', required=True)
    ap.add_argument('--out', required=True)
    a = ap.parse_args()
    sage = shutil.which('sage')
    load_out = os.path.join(os.path.dirname(os.path.abspath(a.out)), 'startup_load_row.json')
    cmds = {'sage -c pass': [sage, '-c', 'pass'],
            'sage -python -c pass': [sage, '-python', '-c', 'pass'],
            'sage -python import sage.all': [sage, '-python', '-c', 'import sage.all'],
            'sage profile_n.sage --mode load (v3 arm loads)': [
                sage, os.path.join(HERE, 'profile_n.sage'), '--mode', 'load', '--point', 'none', '--scalar', '0',
                '--rng-seed', 'none', '--lib', a.lib, '--out', load_out]}
    out = {'kind': 'untimed diagnostic: Sage start-up per launch (no claim)', 'cpu': a.cpu, 'reps': a.reps,
           'launches': {}}
    for rep in range(a.reps):
        for name, argv in cmds.items():
            out['launches'].setdefault(name, []).append(launch(argv, a.cpu))
    out['summary'] = {name: {'wall_s_mean': sum(r['wall_s'] for r in rs) / len(rs),
                             'child_cpu_s_mean': sum(r['child_cpu_s'] for r in rs) / len(rs),
                             'all_exit_0': all(r['returncode'] == 0 for r in rs)}
                      for name, rs in out['launches'].items()}
    json.dump(out, open(a.out, 'w'), indent=1, sort_keys=True)
    print(json.dumps(out['summary'], indent=1))


if __name__ == '__main__':
    main()
