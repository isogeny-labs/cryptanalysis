# Untimed diagnostic: where the baseline arm N's cold CPU goes (no claim, no gate).
#
#   sage profile_n.sage --mode load|timers|cprofile --point ID --scalar S --rng-seed STR --lib SO --out FILE
#
# The baseline is arm N of ../../volcano-n19-native-tau6-v3-20261020/arm.sage (the current n = 19
# row, run 39387473809). This script loads that file's definitions unchanged (its last line,
# `main()`, is stripped and the rest is preparsed and executed here), then:
#
#   --mode timers    runs N's setup and tauDlp once with the ordinary intervals (as the arm does),
#                    then once more through an instrumented copy of setup and of tauDlp /
#                    tauRelationNative that accumulates time.process_time() per stage. The
#                    instrumented run must reproduce the plain run's targets, gb_calls,
#                    spurious, relations, log and ordered relation digest, or the script exits 1.
#   --mode load      only loads the definitions (start-up probe), writes the record and exits.
#   --mode cprofile  runs N's setup and tauDlp under cProfile (separately) and records the top
#                    functions by total and cumulative time.
#
# Every number here is a diagnostic on one runner; the instrumented stages carry their own
# timer overhead (two process_time() calls per stage entry, about 0.1-0.3 us each).
import cProfile
import io
import json
import os
import pstats
import random
import sys
import time

T0 = time.perf_counter()
C0 = time.process_time()
HERE = os.path.dirname(os.path.abspath(sys.argv[0]))
V3 = os.path.join(os.path.dirname(os.path.dirname(HERE)), 'volcano-n19-native-tau6-v3-20261020')
ARM = os.path.join(V3, 'arm.sage')
_argv = list(sys.argv)
sys.argv = [ARM]
_code = open(ARM).read().rstrip()
assert _code.endswith('\nmain()'), 'v3 arm.sage no longer ends with main()'
exec(preparse(_code[:-len('main()')]), globals())
sys.argv = _argv
T_LOADED = time.perf_counter()
C_LOADED = time.process_time()


def opt(k, d=None):
    a = sys.argv[1:]
    return a[a.index(k) + 1] if k in a else d


def plain_run(lib, scalar, seed):
    del RELS[:]
    bind_solve(tauRelationNative)
    cur, P, su_cpu, _ = setup('N', lib)
    Q = scalar * P
    c0 = time.process_time()
    st = tauDlp(cur, P, Q, random.Random(seed))
    on = time.process_time() - c0
    lam = tauEigen(cur, P)
    return {'setup_cpu_s': su_cpu, 'online_cpu_s': on, 'cold_cpu_s': su_cpu + on,
            'counts': {f: rd.plain(st[f]) for f in ('targets', 'gb_calls', 'spurious', 'relations', 'log')},
            'tauDlp_stats': rd.plain({k: st[k] for k in ('gb_cpu_s', 'relation_cpu_s', 'linalg_cpu_s',
                                                         'total_cpu_s')}),
            'digest': rd.relation_digests(RELS, lam, cur.p)}


class Acc:
    def __init__(self):
        self.t = {}
        self.n = {}

    def add(self, k, dt):
        self.t[k] = self.t.get(k, 0.0) + dt
        self.n[k] = self.n.get(k, 0) + 1


def timed_setup(lib, A):
    pt = time.process_time
    c = pt()
    fld = NativeTauField(N_BITS, MODULUS, 6)
    A.add('setup.field_GF(2^19)', pt() - c)
    # TauCurve.__init__, split into its loops (same code as tau.sage).
    c = pt()
    cur = TauCurve.__new__(TauCurve)
    F = fld.F
    n = fld.n
    cur.fld, cur.b = fld, F(1)
    cur.E = EllipticCurve(F, [1, 0, 0, 0, 1])
    cur.N, cur.h, cur.p = ORDER, COFACTOR, ORDER // COFACTOR
    A.add('setup.curve.EllipticCurve', pt() - c)
    c = pt()
    enc = lambda e: ZZ(e.polynomial().change_ring(ZZ)(2))
    base = {}
    for cc in range(1, 2 ** fld.k):
        x = fld.fromBits([(cc >> i) & 1 for i in range(fld.k)])
        rhs = x + 1 / x ** 2
        if rhs.trace() == 0:
            base[x] = cur.E(x, x * halfTraceTau(rhs, n))
    A.add('setup.curve.V_points(trace,halftrace)', pt() - c)
    c = pt()
    cur.reps, cur.repOf = [], {}
    for x in sorted(base, key=enc):
        orbit = [x ** (2 ** e) for e in range(n)]
        rx = min(orbit, key=enc)
        if rx not in cur.repOf:
            cur.repOf[rx] = len(cur.reps)
            ry = cur.E.lift_x(rx)
            cur.reps.append(cur.E(rx, ry[1]))
    A.add('setup.curve.orbit_reps(lift_x)', pt() - c)
    c = pt()
    cur.base = {}
    for x, Pp in base.items():
        orbit = [x ** (2 ** e) for e in range(n)]
        rx = min(orbit, key=enc)
        col = cur.repOf[rx]
        Rp = cur.reps[col]
        for e in range(n):
            T = cur.E(Rp[0] ** (2 ** e), Rp[1] ** (2 ** e))
            if T == Pp:
                cur.base[x] = (Pp, col, e, 1)
                break
            if T == -Pp:
                cur.base[x] = (Pp, col, e, -1)
                break
    cur.fbPoints = n * len(cur.base)
    A.add('setup.curve.base_table(frobenius_search)', pt() - c)
    c = pt()
    cur.native = Native(lib, N_BITS, MODULUS, 6)
    A.add('setup.native_ctx(ctypes_load+tau6_new)', pt() - c)
    c = pt()
    cur.enc = make_enc(fld.F)
    A.add('setup.make_enc', pt() - c)
    c = pt()
    P = generator(cur, 'E0')
    A.add('setup.generator(lift_x,cofactor_mul)', pt() - c)
    return cur, P


def timed_relation(cur, R, stats, shifts, A):
    pt = time.process_time
    fld = cur.fld
    n = fld.n
    k = fld.k
    nat = cur.native
    c = pt()
    xr = cur.enc(R[0])
    A.add('online.loop.encode_xR', pt() - c)
    for j in shifts:
        c0 = pt()
        sols = nat.solve(xr, j)
        d = pt() - c0
        stats['gb_cpu_s'] += d
        stats['gb_calls'] += 1
        A.add('online.loop.native_solve(ctypes)', d)
        for ub, wb in sols:
            c = pt()
            x1 = fld.fromBits([(ub >> i) & 1 for i in range(k)])
            x2 = fld.fromBits([(wb >> i) & 1 for i in range(k)])
            inb = x1 in cur.base and x2 in cur.base
            A.add('online.loop.fromBits+base_lookup', pt() - c)
            if not inb:
                stats['spurious'] += 1
                continue
            c = pt()
            P1, col1, e1, sg1 = cur.base[x1]
            P2, col2, e2, sg2 = cur.base[x2]
            T2 = cur.E(P2[0] ** (2 ** j), P2[1] ** (2 ** j))
            A.add('online.loop.frobenius_T2', pt() - c)
            c = pt()
            hit = None
            for s1 in (1, -1):
                for s2 in (1, -1):
                    if hit is None and s1 * P1 + s2 * T2 == R:
                        hit = [(col1, s1 * sg1, e1), (col2, s2 * sg2, (j + e2) % n)]
            A.add('online.loop.point_check(4_sign_combos)', pt() - c)
            if hit is not None:
                return hit
            stats['spurious'] += 1
    return None


def timed_dlp(cur, P, Q, rng, A, extra=10):
    pt = time.process_time
    c = pt()
    p, h, n = cur.p, cur.h, cur.fld.n
    lam = tauEigen(cur, P)
    Fp = GF(p)
    A.add('online.pre.tauEigen+GF(p)', pt() - c)
    ncol = len(cur.reps)
    stats = {'gb_cpu_s': 0.0, 'gb_calls': 0, 'spurious': 0, 'targets': 0}
    rows, rhs = [], []
    shifts = list(range(n))
    rels = []
    while len(rows) < ncol + extra:
        stats['targets'] += 1
        c = pt()
        al, be = rng.randrange(1, int(p)), rng.randrange(1, int(p))
        A.add('online.loop.rng_randrange', pt() - c)
        c = pt()
        R = al * P + be * Q
        A.add('online.loop.target_al*P+be*Q', pt() - c)
        if R.is_zero():
            continue
        c = pt()
        rng.shuffle(shifts)
        A.add('online.loop.rng_shuffle', pt() - c)
        c = pt()
        rel = timed_relation(cur, R, stats, shifts, A)
        A.add('online.loop.tauRelationNative(total)', pt() - c)
        if rel is None:
            continue
        rels.append(rel)
        c = pt()
        row = {}
        for col, sign, e in rel:
            row[col] = row.get(col, Fp(0)) + sign * Fp(lam) ** e
        rows.append(row)
        rhs.append((h * al % p, h * be % p))
        A.add('online.loop.row_assembly(GF(p))', pt() - c)
    c = pt()
    used = sorted({c_ for r in rows for c_ in r})
    idx = {c_: i for i, c_ in enumerate(used)}
    M = matrix(Fp, len(rows), len(used), sparse=True)
    for i, r in enumerate(rows):
        for c_, v in r.items():
            M[i, idx[c_]] += v
    A.add('online.linalg.matrix_build(sparse)', pt() - c)
    c = pt()
    K = M.left_kernel()
    basis = K.basis()
    A.add('online.linalg.left_kernel', pt() - c)
    c = pt()
    s = None
    for v in basis:
        Aa = sum(v[i] * rhs[i][0] for i in range(len(rows)))
        Bc = sum(v[i] * rhs[i][1] for i in range(len(rows)))
        if Bc != 0:
            s = ZZ(-Aa / Bc)
            break
    A.add('online.linalg.log_from_kernel', pt() - c)
    c = pt()
    ok = s is not None and s * P == Q
    A.add('online.post.verify_s*P==Q', pt() - c)
    stats.update({'relations': len(rows), 'log': int(s) if s is not None else None, 'recovered': ok})
    return stats, rels, lam


def top(prof, key, n=40):
    s = io.StringIO()
    st = pstats.Stats(prof, stream=s)
    st.sort_stats(key)
    out = []
    for func, (cc, nc, tt, ct, callers) in sorted(st.stats.items(), key=lambda kv: -kv[1][2 if key == 'tottime'
                                                                                        else 3])[:n]:
        out.append({'func': '%s:%d(%s)' % (os.path.basename(func[0]), func[1], func[2]), 'ncalls': nc,
                    'tottime_s': tt, 'cumtime_s': ct})
    return out


def main():
    lib = os.path.abspath(opt('--lib'))
    scalar, seed, mode = int(opt('--scalar')), opt('--rng-seed'), opt('--mode')
    rec = {'kind': 'untimed diagnostic profile of the baseline arm N (v3 arm.sage); no claim', 'mode': mode,
           'point': opt('--point'), 'scalar': scalar, 'rng_seed': seed,
           'process_start_to_loaded_wall_s': T_LOADED - T0, 'process_start_to_loaded_cpu_s': C_LOADED - C0,
           'affinity': sorted(os.sched_getaffinity(0))}
    if mode == 'load':
        rec['instrumented_reproduces_plain'] = True
    elif mode == 'timers':
        base = plain_run(lib, scalar, seed)
        rec['plain'] = base
        A = Acc()
        c = time.process_time()
        cur, P = timed_setup(lib, A)
        su = time.process_time() - c
        Q = scalar * P
        c = time.process_time()
        st, rels, lam = timed_dlp(cur, P, Q, random.Random(seed), A)
        on = time.process_time() - c
        rec['instrumented'] = {'setup_cpu_s': su, 'online_cpu_s': on, 'cold_cpu_s': su + on,
                               'stages_cpu_s': A.t, 'stage_entries': A.n,
                               'counts': {f: rd.plain(st[f]) for f in ('targets', 'gb_calls', 'spurious',
                                                                       'relations', 'log')},
                               'digest': rd.relation_digests(rels, lam, cur.p)}
        rec['instrumented_reproduces_plain'] = rec['instrumented']['counts'] == base['counts'] and \
            rec['instrumented']['digest'] == base['digest'] and bool(st['recovered'])
    else:
        del RELS[:]
        bind_solve(tauRelationNative)
        pr = cProfile.Profile()
        pr.enable()
        cur, P, _, _ = setup('N', lib)
        pr.disable()
        rec['setup_top_tottime'] = top(pr, 'tottime')
        rec['setup_top_cumtime'] = top(pr, 'cumulative')
        Q = scalar * P
        pr2 = cProfile.Profile()
        pr2.enable()
        st = tauDlp(cur, P, Q, random.Random(seed))
        pr2.disable()
        rec['online_top_tottime'] = top(pr2, 'tottime')
        rec['online_top_cumtime'] = top(pr2, 'cumulative')
        rec['counts'] = {f: rd.plain(st[f]) for f in ('targets', 'gb_calls', 'spurious', 'relations', 'log')}
        rec['instrumented_reproduces_plain'] = bool(st['recovered'])
    open(opt('--out'), 'w').write(rd.dumps(rec, indent=1, sort_keys=True) + '\n')
    print(json.dumps({'point': rec['point'], 'mode': mode, 'ok': rec['instrumented_reproduces_plain']}), flush=True)
    if not rec['instrumented_reproduces_plain']:
        raise SystemExit(1)


main()
