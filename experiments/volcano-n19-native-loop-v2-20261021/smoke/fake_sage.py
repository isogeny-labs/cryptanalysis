#!/usr/bin/env python3
"""Stand-in `sage` for the local dry run (smoke/dryrun_model_sage.py). NOT Sage, NOT evidence.

Answers `sage <v3 arm.sage | arm_n2x.sage> --arm X ...` with a record in the arm's format,
computed by the pure-Python model of tau.sage (tests/model_sage.py, the v3 solve through
ctypes) where the arm computes something (B, N, N2X), from the archives where it only
checks them (O), and by the v3 binding where it runs the solve (selftest: the stand-in's
"Sage variety" is the v3 library's, so S0 here only exercises formats and S0b's plumbing).
N2X runs the real n2x_compare.py on the model and the real native trace.

v2: before answering for arm_n2x.sage, the stand-in executes the real arm_n2x.sage's option
path (`--options-only`) through tests/sage_emulation.py, the way `sage FILE.sage` would, and
exits 1 with the traceback if it fails. v1's stand-in parsed the options itself and never ran
the .sage file, which is why v1's dry run passed while the runner lost every option.
"""
import base64
import hashlib
import json
import os
import random
import sys
import time

EXP = os.environ['N19_EXP']
sys.path.insert(0, os.path.join(EXP, 'tests'))
sys.path.insert(0, EXP)
import model_sage as ms  # noqa: E402
import n2x_compare as nc  # noqa: E402
import verify_receipt as vr  # noqa: E402
rd, nb = vr.rd, vr.nb
_, ARCH, INFO = vr.archived()


def sha(p):
    return hashlib.sha256(open(p, 'rb').read()).hexdigest()


def binding(lib):
    nat = nb.Native(lib, 19, 854355, 6)
    return nb.check_field(nat, 854355, lambda a, b: nb.pymul(a, b, 19, 854355))


def canonical(rel):
    return [[int(c), int(s), int(e)] for c, s, e in rel]


def ic(arm, scalar, seed, lib, newlib):
    c0 = time.process_time()
    cur = ms.Cur(lib)
    P = ms.generator()
    su = time.process_time() - c0
    Q = ms.B.mul(scalar, P)
    c1 = time.process_time()
    log, rels = [], []
    rng = nc.RecRandom(seed)
    st = ms.tau_dlp(cur, P, Q, rng, nc.tracing_relation(ms.tau_relation, cur.enc, log, rels, canonical))
    row = {f: st[f] for f in vr.COUNT_FIELDS}
    rr = [canonical(r) for r in rels]
    if arm == 'N2X':
        nat = ms.native_trace(newlib, scalar, seed)
        out = nc.compare_setup(nat, list(P), [list(r) for r in cur.reps],
                               [[x, v[0][0], v[0][1], v[1], v[2], v[3]] for x, v in cur.base.items()], st['lambda'],
                               list(Q))
        targets = nc.assemble_targets(rng.calls, log)
        out.update(nc.compare_targets(nat, targets, row, st['recovered'], rr))
        _, _, used = nc.rows_and_rhs(targets, st['lambda'], ms.P_ORD, ms.H)
        out.update(nc.compare_kernel(nat, used, st['basis'], st['kernel_index'], st['log']))
        row.update({'plant': out, 'native_relations_digest': nat['relations_digest'],
                    'reps': [list(r) for r in cur.reps], 'v3_native_sha256': sha(lib)})
    on = time.process_time() - c1
    row.update({'recovered': st['recovered'], 'setup_cpu_s': su, 'online_cpu_s': on, 'cold_cpu_s': su + on,
                'cold_wall_s': su + on, 'relation_cpu_s': on, 'linalg_cpu_s': 0.0, 'gb_cpu_s': 0.0,
                'orbits': 29, 'v_points': 33, 'relations_raw': rr,
                'relations_digest': rd.relation_digests(rr, st['lambda'], ms.P_ORD), 'lambda': st['lambda'],
                'P': INFO['P'] if list(P) == [vr_parse(INFO['P'][0]), vr_parse(INFO['P'][1])] else ['?', '?'],
                'correct': st['recovered'] and st['log'] == scalar % ms.P_ORD})
    return row


def vr_parse(s):
    v = 0
    for t in s.replace(' ', '').split('+'):
        v |= 1 if t == '1' else 2 if t == 'z' else 1 << int(t.split('^')[1])
    return v


def selftest(lib):
    nat = nb.Native(lib, 19, 854355, 6)
    v1 = [(14743, 17), (400912, 3), (465769, 4), (59034, 9), (453846, 18), (480552, 5), (486489, 8)]
    systems = [('v1', x, j) for x, j in v1]
    for src, seed in (('v2', 'volcano-n19-native-tau6-v2-20261019:selftest'),
                      ('new', 'volcano-n19-native-tau6-v3-20261020:selftest')):
        r = random.Random(seed)
        systems += [(src, r.randrange(1, 2 ** 19), t % 19) for t in range(300)]
    multi = json.load(open(os.path.join(vr.V3, 'inputs', 'multi_systems.json')))['systems']
    systems += [('multi', int(x), int(j)) for x, j, _ in multi]
    det = []
    for src, x, j in systems:
        v = [list(t) for t in nat.solve(x, j)]
        det.append({'src': src, 'xR': x, 'j': j, 'sage': v, 'native': v,
                    'bruteforce': [list(t) for t in nat.bruteforce(x, j)], 'third': None if src == 'multi' else v})
    n, n3 = len(det), len(det) - len(multi)
    return {'systems': n, 'set_equal': n, 'order_equal': n, 'bruteforce_equal': n, 'third_checked': n3,
            'third_equal': n3, 'ok': True, 'detail': det, 'detail_sha256': rd.sha256_json(det), 'correct': True}


def main():
    a = sys.argv[2:]
    opt = lambda k: a[a.index(k) + 1] if k in a else None
    arm, lib = opt('--arm'), opt('--lib')
    raw = {'arm': arm, 'serial': int(opt('--serial')), 'point': opt('--point'), 'pid': os.getpid(),
           'affinity': sorted(os.sched_getaffinity(0))}
    v3lib = opt('--v3lib') or lib
    if lib:
        raw['native_sha256'] = sha(lib)
    if arm in ('B', 'N', 'N2X'):
        s = int(opt('--scalar'))
        raw.update({'scalar': s, 'rng_seed': opt('--rng-seed'), 'warm': False})
        raw.update(ic(arm, s, opt('--rng-seed'), v3lib, lib))
        if arm == 'B':
            raw.pop('native_sha256', None)
    elif arm == 'rho':
        raw.update({'scalar': int(opt('--scalar')), 'rng_seed': opt('--rng-seed'), 'verified_reps': 64,
                    'reps': [{'correct': True}] * 64, 'cpu_s': 0.004, 'cpu_s_total': 0.256, 'group_ops_total': 30000,
                    'correct': True})
        raw.pop('native_sha256', None)
    elif arm == 'O':
        insts = [{'instance': i, 'equal': True, 'relations_raw': v['relations_raw'],
                  'relations_digest': v['relations_digest']} for i, v in enumerate(vr.v3_o1_instances())]
        raw.update({'all_equal': True, 'P_equal_archive': True, 'lambda_equal_archive': True, 'lambda': 41811,
                    'digests_computed': 10, 'instances': insts, 'correct': True})
    elif arm == 'selftest':
        raw.update(selftest(lib))
    if arm in ('N', 'N2X', 'O', 'selftest'):
        raw['binding_check'] = binding(v3lib if arm == 'N2X' else lib)
        if arm == 'N2X':
            raw['binding_check_newlib'] = binding(lib)
    b = json.dumps(raw, sort_keys=True, separators=(',', ':')).encode()
    open(opt('--out'), 'wb').write(b + b'\n')
    print('raw_b64=' + base64.b64encode(b).decode())
    print('raw_result_sha256=%s serial=%d arm=%s point=%s correct=%d' % (
        hashlib.sha256(b).hexdigest(), raw['serial'], arm, raw['point'], int(bool(raw.get('correct')))))


def option_path_first():
    script, args = sys.argv[1], sys.argv[2:]
    if not script.endswith('arm_n2x.sage'):
        return
    import tempfile
    import traceback
    import sage_emulation as se
    with tempfile.TemporaryDirectory() as t:
        a = list(args)
        a[a.index('--out') + 1] = os.path.join(t, 'options.json')
        r = se.run_sage_file(script, a + ['--options-only'])
    if r.exc is not None:
        traceback.print_exception(r.exc)
        raise SystemExit(1)


option_path_first()
main()
