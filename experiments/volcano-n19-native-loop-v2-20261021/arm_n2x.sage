# Planted positive control N2X of volcano-n19-native-loop-v2-20261021 (one process = one row).
#
#   sage arm_n2x.sage --arm N2X --serial K --point ID --scalar S --rng-seed STR --lib NEWLIB --v3lib V3LIB --out FILE
#   ... --options-only   load the v3 definitions, parse and echo every option to FILE, solve nothing
#
# v2 changes against v1 (volcano-n19-native-loop-20261021): the v3 definitions are executed by
# _exec_v3_definitions, which keeps the caller's argv in a function local (v1 lost every option,
# see that function), a missing option exits with its name, and --options-only exists.
#
# N2X = the candidate N2 (the whole pipeline in native code, through libtau6loop.so's
# tau6loop_dlp_trace, the same crate as the tau6dlp binary) PLUS the work N2 removes, redone:
# the baseline arm N's whole Sage path (the unmodified ../volcano-ic/tau.sage tauDlp with
# tauRelationNative and the v3 library, through ../volcano-n19-native-tau6-v3-20261020/arm.sage's
# own definitions) on the same point, and Sage's linear algebra (M.left_kernel().basis()).
# Every item is compared and any difference aborts the process (exit 1):
#
#   setup    the generator P, the 29 orbit representatives (Sage's lift_x y), the base
#            table x -> (point, column, e, sign) of all 33 V' points, lambda;
#   per target, in order: (al, be) as Sage's rng drew them, R = al P + be Q (or zero),
#            the shift order after shuffle, the number of shift systems solved, and the
#            decomposition returned (or none);
#   totals   targets, gb_calls, spurious, relations, log, recovered, ordered relations;
#   algebra  the used columns, Sage's left-kernel echelon basis (every vector, every entry),
#            the index of the first basis vector with B != 0, and the log.
#
# Intervals as in arm N: setup = target-independent construction (Sage's setup('N') and
# the native setup inside tau6loop_dlp_trace are both inside N2X's cold interval, as is the
# comparison); cold = setup + online, time.process_time().
import ctypes
import hashlib
import json
import os
import random
import sys
import time

T_START = time.perf_counter()
HERE_N2X = os.path.dirname(os.path.abspath(sys.argv[0]))      # (the v3 code below redefines MYDIR)
V3 = os.path.join(os.path.dirname(HERE_N2X), 'volcano-n19-native-tau6-v3-20261020')
ARM3 = os.path.join(V3, 'arm.sage')


def _exec_v3_definitions(path, namespace):
    """Execute v3 arm.sage minus its last line `main()` in `namespace`, with sys.argv = [path].

    The caller's argv is kept in this function's local `saved`. v1 kept it in the module
    global `_argv`, and v3 arm.sage line 62 (`_argv = sys.argv`, executed in these same
    globals) rebound it to [path], so v1's `sys.argv = _argv` restored [path] and every
    option was lost (run 39526183111, smoke serials 9 and 16). Code executed in `namespace`
    cannot rebind a local of this function.
    """
    saved = list(sys.argv)
    sys.argv = [path]
    try:
        code = open(path).read().rstrip()
        assert code.endswith('\nmain()'), 'v3 arm.sage no longer ends with main()'
        exec(preparse(code[:-len('main()')]), namespace)   # v3 definitions, unchanged (arm N's code)
    finally:
        sys.argv = saved


_exec_v3_definitions(ARM3, globals())
T_LOADED = time.perf_counter()


sys.path.insert(0, HERE_N2X)
import n2x_compare as nc          # plain Python, never preparsed

TARGET_LOG = []


def native_trace(newlib, scalar, seed):
    lib = ctypes.CDLL(newlib)
    lib.tau6loop_dlp_trace.restype = ctypes.c_int64
    lib.tau6loop_dlp_trace.argtypes = [ctypes.c_uint64, ctypes.c_char_p, ctypes.c_size_t, ctypes.c_char_p,
                                       ctypes.c_size_t]
    sb = seed.encode()
    cap = int(1 << 22)
    while True:
        buf = ctypes.create_string_buffer(cap)
        n = int(lib.tau6loop_dlp_trace(int(scalar), sb, len(sb), buf, cap))
        if n < 0:
            raise SystemExit('tau6loop_dlp_trace refused its arguments')
        if n <= cap:
            return json.loads(buf.raw[:n].decode())
        cap = n


def compare(cur, P, Q, st, rng, nat, lam):
    enc = lambda e: int(cur.enc(e))
    out = nc.compare_setup(nat, [enc(P[0]), enc(P[1])], [[enc(R0[0]), enc(R0[1])] for R0 in cur.reps],
                           [[enc(x), enc(v[0][0]), enc(v[0][1]), int(v[1]), int(v[2]), int(v[3])]
                            for x, v in cur.base.items()], int(lam), [enc(Q[0]), enc(Q[1])])
    targets = nc.assemble_targets(rng.calls, TARGET_LOG)
    counts = {f: (None if st[f] is None else int(st[f])) for f in ('targets', 'gb_calls', 'spurious', 'relations',
                                                                  'log')}
    out.update(nc.compare_targets(nat, targets, counts, bool(st['recovered']),
                                  [rd.canonical_relation(r) for r in RELS]))
    # Sage's linear algebra, as tauDlp builds it, from Sage's own draws and relations
    p, h = int(cur.p), int(cur.h)
    rows, rhs, used = nc.rows_and_rhs(targets, int(lam), p, h)
    Fp = GF(p)
    idx = {c: i for i, c in enumerate(used)}
    M = matrix(Fp, len(rows), len(used), sparse=True)
    for i2, r in enumerate(rows):
        for c, v in r.items():
            M[i2, idx[c]] += Fp(v)
    basis = M.left_kernel().basis()
    s, kidx = None, None
    for bi, v in enumerate(basis):
        A = sum(v[i2] * rhs[i2][0] for i2 in range(len(rows)))
        Bc = sum(v[i2] * rhs[i2][1] for i2 in range(len(rows)))
        if Bc != 0:
            s, kidx = int(ZZ(-A / Bc)), int(bi)
            break
    out.update(nc.compare_kernel(nat, used, [[int(x) for x in v] for v in basis], kidx, s))
    return out


REQUIRED = ('--arm', '--serial', '--point', '--scalar', '--rng-seed', '--lib', '--v3lib', '--out')


def main():
    a = sys.argv[1:]
    opt = lambda k, d=None: a[a.index(k) + 1] if k in a else d
    missing = [k for k in REQUIRED if opt(k) is None]
    if missing:
        raise SystemExit('arm_n2x.sage: missing option(s) %s; sys.argv = %r' % (' '.join(missing), sys.argv))
    arm, out, lib, v3lib = opt('--arm'), opt('--out'), os.path.abspath(opt('--lib')), os.path.abspath(opt('--v3lib'))
    assert arm == 'N2X'
    scalar, seed = int(opt('--scalar')), opt('--rng-seed')
    if '--options-only' in a:   # the smoke job's Sage option-path check: parse, echo, run nothing
        rec = {'script': 'arm_n2x.sage', 'argv': list(sys.argv), 'options': {k: opt(k) for k in REQUIRED},
               'lib_exists': os.path.isfile(lib), 'v3lib_exists': os.path.isfile(v3lib),
               'v3_definitions_loaded': all(callable(globals().get(f)) for f in
                                            ('setup', 'tauDlp', 'tauRelationNative', 'binding_check', 'tauEigen'))}
        with open(out, 'w') as f:
            f.write(json.dumps(rec, sort_keys=True) + '\n')
        print('options_ok ' + json.dumps(rec, sort_keys=True), flush=True)
        return
    row = {'arm': arm, 'serial': int(opt('--serial')), 'point': opt('--point'), 'pid': os.getpid(),
           'affinity': sorted(os.sched_getaffinity(0)),
           'process_time_resolution_s': time.get_clock_info('process_time').resolution,
           'load_wall_s': T_LOADED - T_START, 'native_sha256': sha256_file(lib), 'v3_native_sha256': sha256_file(v3lib),
           'scalar': scalar, 'rng_seed': seed, 'warm': False}
    del RELS[:]
    del TARGET_LOG[:]
    tauDlp.__globals__['tauRelation'] = nc.tracing_relation(tauRelationNative, lambda e: cur.enc(e), TARGET_LOG,
                                                            RELS, rd.canonical_relation)
    c0, w0 = time.process_time(), time.perf_counter()
    cur, P, _, _ = setup('N', v3lib)                     # arm N's setup (Sage)
    setup_cpu, setup_wall = time.process_time() - c0, time.perf_counter() - w0
    Q = scalar * P                                       # fixture, outside every interval
    c1, w1 = time.process_time(), time.perf_counter()
    rng = nc.RecRandom(seed)
    st = tauDlp(cur, P, Q, rng)                          # arm N's online path (Sage)
    nat = native_trace(lib, scalar, seed)                # N2's pipeline (native, setup included)
    lam = tauEigen(cur, P)
    try:
        plant = compare(cur, P, Q, st, rng, nat, lam)
    except nc.Mismatch as e:
        raise SystemExit('PLANT MISMATCH (N2 vs Sage): %s' % e)
    online_cpu, online_wall = time.process_time() - c1, time.perf_counter() - w1
    row.update(rd.plain({f: st[f] for f in ('targets', 'gb_calls', 'spurious', 'relations', 'log', 'recovered',
                                            'orbits', 'v_points', 'gb_cpu_s', 'relation_cpu_s', 'linalg_cpu_s',
                                            'total_cpu_s')}))
    row.update({'setup_cpu_s': setup_cpu, 'setup_wall_s': setup_wall, 'online_cpu_s': online_cpu,
                'online_wall_s': online_wall, 'cold_cpu_s': setup_cpu + online_cpu,
                'cold_wall_s': setup_wall + online_wall,
                'correct': bool(st['recovered']) and st['log'] is not None and int(st['log']) == scalar % int(cur.p),
                'relations_digest': rd.relation_digests(RELS, lam, cur.p),
                'relations_raw': [rd.canonical_relation(r) for r in RELS],
                'P': [str(P[0]), str(P[1])], 'lambda': int(lam),
                'reps': [[int(cur.enc(R0[0])), int(cur.enc(R0[1]))] for R0 in cur.reps],
                'native_relations_digest': nat['relations_digest'], 'plant': plant})
    row['binding_check'] = binding_check(v3lib)          # v3's field check, after every interval
    row['binding_check_newlib'] = binding_check(lib)     # the same check on libtau6loop.so's tau6_* ABI
    row['correct'] = bool(row['correct']) and row['binding_check']['ok'] and row['binding_check_newlib']['ok']
    raw = rd.dumps(row, sort_keys=True, separators=(',', ':')).encode()
    with open(out, 'wb') as f:
        f.write(raw + b'\n')
    print('raw_b64=' + base64.b64encode(raw).decode(), flush=True)
    print('raw_result_sha256=%s serial=%d arm=%s point=%s correct=%d' %
          (hashlib.sha256(raw).hexdigest(), row['serial'], arm, row['point'], int(bool(row.get('correct')))),
          flush=True)
    if not row.get('correct'):
        raise SystemExit(3)


main()
