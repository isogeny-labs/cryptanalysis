"""Sage option-path check (the smoke job's first Sage step; untimed; a hard gate before anything else).

    sage -python option_check.py --lib SO --v3lib SO --bin EXE --out-dir DIR

v1's planted arm and profile lost every command-line option under the real `sage FILE.sage`
(run 39526183111) although every local check passed, because no local check executed the
.sage files under Sage. This script runs, under the pinned image's own `sage`:

* arm_n2x.sage with the exact command run_schedule.py builds for each N2X run of the smoke
  part and for the first and last N2X runs of the timed part, plus `--options-only` (the v3
  definitions are loaded exactly as in a real run, then every option is parsed and echoed,
  nothing is solved);
* diagnosis/profile_n.sage --mode load with the profile step's options.

Each launch must exit 0 and echo argv and every option exactly as passed. Otherwise it prints
`OPTION-PATH CHECK FAILED: ...` (the script, the exit code and the stderr tail) and exits 1, so
the job stops before the profile, the smoke part and the timed job. DIR/option-check.json
records every launch.
"""
import argparse
import json
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)


def launch(argv, out):
    p = subprocess.run(argv, cwd=HERE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    rec = {'argv': argv, 'returncode': p.returncode, 'stdout_tail': p.stdout.decode(errors='replace')[-600:],
           'stderr_tail': p.stderr.decode(errors='replace')[-1500:]}
    try:
        rec['echo'] = json.load(open(out))
    except (OSError, ValueError):
        rec['echo'] = None
    return rec


def check_n2x(rec, args):
    e = rec['echo']
    if rec['returncode'] != 0 or e is None:
        return 'exit %r, echo %s' % (rec['returncode'], 'missing' if e is None else 'present')
    if e.get('argv', [None])[1:] != args:
        return 'argv after the v3 load differs: %r' % e.get('argv')
    bad = [k for k, v in e['options'].items() if v != args[args.index(k) + 1]]
    if bad:
        return 'options differ: %s' % bad
    if not (e.get('lib_exists') and e.get('v3lib_exists') and e.get('v3_definitions_loaded')):
        return 'library missing or v3 definitions not loaded: %r' % {k: e.get(k) for k in (
            'lib_exists', 'v3lib_exists', 'v3_definitions_loaded')}
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--lib', required=True)
    ap.add_argument('--v3lib', required=True)
    ap.add_argument('--bin', required=True)
    ap.add_argument('--out-dir', required=True)
    a = ap.parse_args()
    a.lib, a.v3lib, a.bin, a.out_dir = (os.path.abspath(x) for x in (a.lib, a.v3lib, a.bin, a.out_dir))
    import run_schedule as rs
    sage = shutil.which('sage')
    os.makedirs(a.out_dir, exist_ok=True)
    sched = json.load(open(os.path.join(HERE, 'schedule.json')))
    n2x = {part: [r for seg in p['segments'] for r in seg['runs'] if r['arm'] == 'N2X']
           for part, p in sched['parts'].items()}
    picks = [('smoke', r) for r in n2x['smoke']] + [('timed', n2x['timed'][0]), ('timed', n2x['timed'][-1])]
    launches, failures = [], []
    for part, run in picks:
        out = os.path.join(a.out_dir, 'n2x-%s-%03d.json' % (part, run['serial']))
        cmd = rs.command(sage, run, part, a, out, a.out_dir) + ['--options-only']
        rec = launch(cmd, out)
        rec['check'] = 'arm_n2x.sage %s serial %d' % (part, run['serial'])
        why = check_n2x(rec, cmd[2:])
        rec['ok'] = why is None
        launches.append(rec)
        if why:
            failures.append('%s: %s | stderr: %s' % (rec['check'], why, rec['stderr_tail'][-400:]))
    pt = sched['parts']['smoke']
    sp = next(r for seg in pt['segments'] for r in seg['runs'] if r.get('point'))
    out = os.path.join(a.out_dir, 'profile-load.json')
    pargs = ['--mode', 'load', '--point', sp['point'], '--scalar', str(sp['scalar']), '--rng-seed', sp['rng_seed'],
             '--lib', a.v3lib, '--out', out]
    rec = launch([sage, os.path.join(HERE, 'diagnosis', 'profile_n.sage')] + pargs, out)
    rec['check'] = 'diagnosis/profile_n.sage --mode load'
    e = rec['echo'] or {}
    why = None
    if rec['returncode'] != 0 or not e:
        why = 'exit %r' % rec['returncode']
    elif e.get('argv', [None])[1:] != pargs or e.get('point') != sp['point'] or not e.get('lib_exists'):
        why = 'argv, point or library differ: %r' % {k: e.get(k) for k in ('argv', 'point', 'lib_exists')}
    rec['ok'] = why is None
    launches.append(rec)
    if why:
        failures.append('%s: %s | stderr: %s' % (rec['check'], why, rec['stderr_tail'][-400:]))
    res = {'kind': 'Sage option-path check (untimed gate, before the profile and the smoke part)',
           'sage': sage, 'passed': not failures, 'failures': failures, 'launches': launches}
    with open(os.path.join(a.out_dir, 'option-check.json'), 'w') as f:
        f.write(json.dumps(res, indent=1, sort_keys=True) + '\n')
    if failures:
        print('OPTION-PATH CHECK FAILED: %d of %d launches\n  %s' % (len(failures), len(launches),
                                                                    '\n  '.join(failures)), file=sys.stderr)
        sys.exit(1)
    print('option-path check passed: %d launches (%s)' % (len(launches), ', '.join(r['check'] for r in launches)))


if __name__ == '__main__':
    main()
