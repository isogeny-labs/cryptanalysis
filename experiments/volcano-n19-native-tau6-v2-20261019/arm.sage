# One process = one row of the frozen schedule (protocol.json, schedule.json), protocol v2.
#
# v2 differs from ../volcano-n19-native-tau6-20261019/arm.sage (v1) in:
#   - the ctypes binding lives in native_binding.py (plain Python, so the
#     local checks run the same binding) and passes the modulus as Sage
#     reads it (run.sage MODULUS is lowest degree first). v1 passed the
#     reciprocal polynomial, which failed S0 of run 39307409409
#     (diagnosis/README.md);
#   - every native process checks the context's field against Sage's
#     (modulus and 256 products) after its timed intervals; a mismatch makes
#     the row incorrect;
#   - S0 checks the 7 v1 mismatch systems and 300 new ones with three
#     evaluators (Sage Groebner variety, native, and a direct S3 evaluation
#     in Sage's field arithmetic over all 4,096 pairs), plus every
#     multi-solution system of the field (diagnosis/multi_systems.json) for
#     the order, and records every system;
#   - the native variety comes in Sage's order (ascending (w, u); lib.rs),
#     so B and N return the same relation even from a multi-solution
#     system, and the gates compare ordered decompositions too.
#
#   sage arm.sage --arm B|N|Naa|NX|rho --point ID --scalar S --rng-seed STR --lib SO --out FILE
#   sage arm.sage --arm O --lib SO --out FILE            archived exactness (no timing claim)
#   sage arm.sage --arm selftest --lib SO --out FILE     Sage variety == native on random systems
#
# Arms (protocol.json "arms"):
#   B    baseline: the unmodified ../volcano-ic/tau.sage (TauField, TauCurve,
#        tauDlp, tauRelation with PolyBoRi Groebner + variety per shift).
#   N    candidate: the same tauDlp, with the global tauRelation rebound to
#        tauRelationNative, whose only change is that the variety of the
#        shift system comes from ../native (Rust, ctypes) instead of
#        TauField.system + ideal + groebner_basis + variety. Its setup
#        builds NativeTauField (no Boolean ring) instead of TauField.
#   Naa  A/A: a second process of N.
#   NX   planted positive control: N plus the removed work, redone: on every
#        shift system the Sage system, Groebner basis and variety are
#        computed and compared with the native variety (abort on any
#        difference), then discarded.
#   rho  the matched signed-Frobenius rho of volcano-ic/rho-arm-20261014
#        (rho_frob.py SageBackend, R = 16, 64 reps), for the S unit and gap.
#
# Timing: time.process_time() (CPU, the baseline row's measure) and
# perf_counter (wall). setup = target-independent construction; online =
# tauDlp (first target-dependent operation .. verified log); cold = setup +
# online. Sage import and source loading precede both and are recorded by
# the launcher, not here. Q = s * P is fixture construction outside every
# interval (as in rho-arm-20261014).

import hashlib
import json
import os
import random
import sys
import time
import ctypes

T_PROC0 = time.perf_counter()
MYDIR = os.path.dirname(os.path.abspath(sys.argv[0]))
VIC = os.path.join(os.path.dirname(MYDIR), 'volcano-ic')
RHODIR = os.path.join(VIC, 'rho-arm-20261014')

_argv = sys.argv
sys.argv = [os.path.join(VIC, 'run.sage')]
load(os.path.join(VIC, 'run.sage'))
sys.argv = _argv
load(os.path.join(VIC, 'tau.sage'))
sys.path.insert(0, RHODIR)
import rho_frob as rf
sys.path.insert(0, MYDIR)
import native_binding as nb

NATIVE_MODULUS = nb.modulus_int(MODULUS)  # run.sage MODULUS: lowest degree first, as R(MODULUS) reads it

T_LOADED = time.perf_counter()
_tauRelationSage = tauRelation          # the baseline's solve, kept for B and NX
RELS = []                               # every relation returned (gate data; outside nothing, appended in O(1))
PLANT = {'checked_calls': 0, 'sage_solutions': 0, 'multi_solution_calls': 0, 'order_agree_calls': 0}


def sha256_file(path):
    return hashlib.sha256(open(path, 'rb').read()).hexdigest()


def jplain(o):
    try:
        return int(o) if o == int(o) and not isinstance(o, float) else float(o)
    except (TypeError, ValueError):
        return str(o)


def Native(path, n, modulus_coeffs, k):
    """The v2 binding (native_binding.py), with run.sage's MODULUS read lowest degree first."""
    return nb.Native(path, n, nb.modulus_int(modulus_coeffs), k)


def sage_modulus_int(F):
    """F.modulus() as an integer, bit i = coefficient of z^i (Sage's own report of its field)."""
    return sum(int(c) << i for i, c in enumerate(F.modulus().list()))


def binding_check(lib):
    """Untimed, after the row's intervals: the native context's field is Sage's field."""
    R = PolynomialRing(GF(2), 'Z')
    F = GF(2 ** N_BITS, 'z', modulus=R(MODULUS))
    enc = make_enc(F)
    nat = Native(lib, N_BITS, MODULUS, 6)
    rec = nb.check_field(nat, sage_modulus_int(F), lambda a, b: enc(F.from_integer(a) * F.from_integer(b)))
    rec['run_sage_modulus_lowest_first'] = NATIVE_MODULUS
    rec['ok'] = rec['ok'] and NATIVE_MODULUS == rec['expected_modulus']
    return rec


class NativeTauField:
    """TauField without the Boolean ring and the shift systems (the native
    solve does not need them): the same F, z, n, k and fromBits."""

    def __init__(self, n, modulus, k):
        R = PolynomialRing(GF(2), 'Z')
        self.F = GF(2 ** n, 'z', modulus=R(modulus))
        self.z = self.F.gen()
        self.n, self.k = n, k

    def fromBits(self, bits):
        return sum(self.z ** i for i in range(self.k) if bits[i])


def make_enc(F):
    x = F.gen()
    try:
        x.to_integer()
        return lambda e: int(e.to_integer())
    except AttributeError:
        return lambda e: int(ZZ(e.polynomial().change_ring(ZZ)(2)))


def tauRelationNative(cur, R, stats, shifts):
    """tau.sage tauRelation with the variety from the native solve."""
    fld = cur.fld
    n = fld.n
    k = fld.k
    nat = cur.native
    xr = cur.enc(R[0])
    for j in shifts:
        c0 = time.process_time()
        sols = nat.solve(xr, j)
        stats['gb_cpu_s'] += time.process_time() - c0
        stats['gb_calls'] += 1
        for ub, wb in sols:
            x1 = fld.fromBits([(ub >> i) & 1 for i in range(k)])
            x2 = fld.fromBits([(wb >> i) & 1 for i in range(k)])
            if x1 not in cur.base or x2 not in cur.base:
                stats['spurious'] += 1
                continue
            P1, col1, e1, sg1 = cur.base[x1]
            P2, col2, e2, sg2 = cur.base[x2]
            T2 = cur.E(P2[0] ** (2 ** j), P2[1] ** (2 ** j))
            for s1 in (1, -1):
                for s2 in (1, -1):
                    if s1 * P1 + s2 * T2 == R:
                        return [(col1, s1 * sg1, e1), (col2, s2 * sg2, (j + e2) % n)]
            stats['spurious'] += 1
    return None


def sage_variety(fld, j, xR, b):
    """The baseline's per-shift solve (tau.sage tauRelation), as (u, w) bit pairs in Sage's order."""
    polys = [f for f in fld.system(j, xR, b) if f != 0]
    I = ideal(polys)
    gb = I.groebner_basis()
    sols = I.variety() if gb != [1] else []
    out = []
    for sol in sols:
        ub = sum(int(sol[g]) << i for i, g in enumerate(fld.u))
        wb = sum(int(sol[g]) << i for i, g in enumerate(fld.w))
        out.append((int(ub), int(wb)))
    return out


class PlantedNative:
    """NX: the native solve plus the work it removes, redone. On every shift system
    the baseline's Sage system, Groebner basis and variety are computed and
    compared with the native variety (abort on any difference); the native
    result is what the candidate's tauRelationNative then uses."""

    def __init__(self, inner, fld, b):
        self.inner, self.fld, self.b = inner, fld, b

    def solve(self, xr, j):
        ref = sage_variety(self.fld, j, self.fld.F.from_integer(xr), self.b)
        mine = self.inner.solve(xr, j)
        PLANT['checked_calls'] += 1
        PLANT['sage_solutions'] += len(ref)
        if sorted(ref) != sorted(mine):
            raise SystemExit('PLANT MISMATCH: xR %d shift %d sage %r native %r' % (xr, j, ref, mine))
        if len(ref) > 1:
            PLANT['multi_solution_calls'] += 1
            PLANT['order_agree_calls'] += int(ref == mine)
        return mine


def recordingRelation(inner):
    def f(cur, R, stats, shifts):
        rel = inner(cur, R, stats, shifts)
        if rel is not None:
            RELS.append(rel)
        return rel
    return f


def relation_digests(rels, lam, p):
    """ordered: the decompositions as returned; canonical: each decomposition as a
    sorted multiset of (column, sign, Frobenius power) (R = sum of its terms, so
    the order of two terms is not part of the decomposition); rows: the matrix
    rows tauDlp builds from them (column -> sum sign * lambda^e mod p)."""
    ordered = [[list(map(int, t)) for t in r] for r in rels]
    canon = [sorted(r) for r in ordered]
    rows = []
    for r in ordered:
        row = {}
        for col, sg, e in r:
            row[col] = (row.get(col, 0) + sg * pow(int(lam), int(e), int(p))) % int(p)
        rows.append(sorted(row.items()))
    h = lambda o: hashlib.sha256(json.dumps(o, separators=(',', ':')).encode()).hexdigest()
    return {'ordered_sha256': h(ordered), 'canonical_sha256': h(canon), 'rows_sha256': h(rows),
            'count': len(rels)}


def setup(arm, lib):
    """Target-independent construction; the arm's setup interval."""
    c0, w0 = time.process_time(), time.perf_counter()
    if arm == 'B':
        fld = TauField(N_BITS, MODULUS, 6)
        cur = TauCurve(fld, ORDER, COFACTOR)
    elif arm in ('N', 'Naa'):
        fld = NativeTauField(N_BITS, MODULUS, 6)
        cur = TauCurve(fld, ORDER, COFACTOR)
        cur.native = Native(lib, N_BITS, MODULUS, 6)
        cur.enc = make_enc(fld.F)
    elif arm == 'NX':
        fld = TauField(N_BITS, MODULUS, 6)
        cur = TauCurve(fld, ORDER, COFACTOR)
        cur.native = PlantedNative(Native(lib, N_BITS, MODULUS, 6), fld, fld.F(1))
        cur.enc = make_enc(fld.F)
    else:
        raise ValueError(arm)
    P = generator(cur, 'E0')
    return cur, P, time.process_time() - c0, time.perf_counter() - w0


def bind_solve(fn):
    """Rebind the global tauRelation that tau.sage's tauDlp calls."""
    tauDlp.__globals__['tauRelation'] = recordingRelation(fn)


def ic_row(arm, scalar, seed, lib):
    bind_solve(_tauRelationSage if arm == 'B' else tauRelationNative)
    cur, P, setup_cpu, setup_wall = setup(arm, lib)
    Q = scalar * P                                  # fixture, outside every interval
    c0, w0 = time.process_time(), time.perf_counter()
    st = tauDlp(cur, P, Q, random.Random(seed))
    online_cpu, online_wall = time.process_time() - c0, time.perf_counter() - w0
    lam = tauEigen(cur, P)
    row = {k: jplain(v) for k, v in st.items()}
    row.update({'setup_cpu_s': setup_cpu, 'setup_wall_s': setup_wall,
                'online_cpu_s': online_cpu, 'online_wall_s': online_wall,
                'cold_cpu_s': setup_cpu + online_cpu, 'cold_wall_s': setup_wall + online_wall,
                'correct': bool(st['recovered']) and st['log'] is not None and int(st['log']) == scalar % int(cur.p),
                'relations_digest': relation_digests(RELS, lam, cur.p),
                'P': [str(P[0]), str(P[1])], 'lambda': int(lam)})
    if arm == 'NX':
        row['plant'] = dict(PLANT)
    if arm in ('N', 'Naa'):
        row['warm_batch'] = warm_batch(arm, scalar, seed, lib, row)
    return row


WARM_SETUP_REPS, WARM_ONLINE_REPS = 20, 3


def warm_batch(arm, scalar, seed, lib, cold):
    """Pre-registered repeated-batch measurement (secondary, warm, after the cold
    interval has been recorded): setup rebuilt WARM_SETUP_REPS times and the
    same point's tauDlp rerun WARM_ONLINE_REPS times (same rng seed, so the same
    relations); means per repetition. Labelled warm; never decides."""
    su = []
    for _ in range(WARM_SETUP_REPS):
        cur, P, c, w = setup(arm, lib)
        su.append(c)
    Q = scalar * P
    on = []
    same = True
    for _ in range(WARM_ONLINE_REPS):
        del RELS[:]
        c0 = time.process_time()
        st = tauDlp(cur, P, Q, random.Random(seed))
        on.append(time.process_time() - c0)
        same = same and st['gb_calls'] == cold['gb_calls'] and bool(st['recovered']) and \
            relation_digests(RELS, cold['lambda'], cur.p)['rows_sha256'] == cold['relations_digest']['rows_sha256']
    return {'label': 'repeated-batch, warm (secondary)', 'setup_reps': WARM_SETUP_REPS,
            'setup_cpu_s_mean': sum(su) / len(su), 'online_reps': WARM_ONLINE_REPS,
            'online_cpu_s_mean': sum(on) / len(on), 'online_cpu_s': on, 'same_relations': same}


def rho_row(scalar):
    proto = json.load(open(os.path.join(RHODIR, 'protocol.json')))
    fldB = Field(N_BITS, MODULUS, K)
    curB = Curve(fldB, 0, fldB.F(1), ORDER, COFACTOR)
    P = generator(curB, 'E0')
    B = rf.SageBackend(curB.E)
    lam = int(tauEigen(curB, P))
    rp = proto['rho']
    c0 = time.process_time()
    tables = [rf.WalkTable(B, P, rp['walk_seed_format'] % k, R=rp['R'])
              for k in range(proto['arms']['rho']['reps_per_scalar'])]
    table_cpu = time.process_time() - c0
    Q = scalar * P
    reps = []
    for k, tb in enumerate(tables):
        r1 = rf.solve(B, P, Q, lam, tb)
        r1['correct'] = bool(r1['verified']) and r1['log'] == scalar % curB.p
        reps.append({f: jplain(r1[f]) for f in ('steps', 'group_ops', 'cpu_s', 'wall_s', 'correct', 'log')})
    n = len(reps)
    return {'reps': reps, 'rho_tables_cpu_s': table_cpu,
            'cpu_s': sum(x['cpu_s'] for x in reps) / n, 'wall_s': sum(x['wall_s'] for x in reps) / n,
            'group_ops_total': sum(x['group_ops'] for x in reps), 'cpu_s_total': sum(x['cpu_s'] for x in reps),
            'steps_mean': sum(x['steps'] for x in reps) / n,
            'verified_reps': sum(1 for x in reps if x['correct']), 'correct': all(x['correct'] for x in reps)}


def archived_row(lib):
    """O: the candidate on the ten archived scalars with the archived rng seeds;
    counts and logs must equal run 38520305068's tau6 rows (Sage)."""
    bind_solve(tauRelationNative)
    proto = json.load(open(os.path.join(RHODIR, 'protocol.json')))
    arch = {r['instance']: r for r in map(json.loads, open(os.path.join(RHODIR, 'results', 'arms.jsonl')))
            if r['arm'] == 'tau6'}
    info = json.load(open(os.path.join(RHODIR, 'results', 'runtime-info.json')))
    cur, P, _, _ = setup('N', lib)
    out = []
    for ii, s in enumerate(proto['scalars']):
        del RELS[:]
        st = tauDlp(cur, P, int(s) * P, random.Random(proto['arms']['tau6']['rng_seed'] % ii))
        a = arch[ii]
        cmp = {f: [jplain(st[f]), a[f]] for f in ('targets', 'gb_calls', 'spurious', 'relations', 'log')}
        out.append({'instance': ii, 'scalar': int(s), 'compare': cmp,
                    'equal': all(x == y for x, y in cmp.values()) and bool(st['recovered']),
                    'native_total_cpu_s': st['total_cpu_s'], 'archived_sage_total_cpu_s': a['total_cpu_s']})
    return {'P_equal_archive': [str(P[0]), str(P[1])] == info['P'], 'instances': out,
            'all_equal': all(o['equal'] for o in out) and [str(P[0]), str(P[1])] == info['P']}


# The seven S0 systems of run 39307409409 where Sage and the v1 native side differed
# (diagnosis/s0_v1_rederived.json): (xR as integer, shift j).
V1_S0_MISMATCHES = [(14743, 17), (400912, 3), (465769, 4), (59034, 9), (453846, 18), (480552, 5), (486489, 8)]


def third_sage(F, xR, j, k=6):
    """Third evaluator: S3(x1, sigma^j(x2), xR) evaluated directly in Sage's field on
    every (u, w); shares no code with tau.sage's TauField or with lib.rs."""
    z = F.gen()
    xs = [F(0) + sum((z ** i for i in range(k) if (c >> i) & 1), F(0)) for c in range(1 << k)]
    x2s = [x ** (2 ** j) for x in xs]
    x2sq = [x * x for x in x2s]
    xR2, one = xR * xR, F(1)
    out = []
    for u, x1 in enumerate(xs):
        x1sq = x1 * x1
        for w, x2 in enumerate(x2s):
            p = x1 * x2
            if p * p + xR2 * (x1sq + x2sq[w]) + xR * p + one == 0:
                out.append((u, w))
    return out


def selftest_row(lib, count=300):
    """S0 (v2): on the 7 v1 mismatch systems and `count` new random (xR, j), the Sage
    variety of TauField.system, the native variety, the native brute force and the
    direct S3 evaluation in Sage's field agree as sets, and Sage's order equals the
    native order; on every multi-solution system of the field (multi_systems.json)
    Sage's and the native variety agree in order. Every system is recorded."""
    fld = TauField(N_BITS, MODULUS, 6)
    nat = Native(lib, N_BITS, MODULUS, 6)
    enc = make_enc(fld.F)
    rng = random.Random('volcano-n19-native-tau6-v2-20261019:selftest')
    systems = [('v1', xr, j) for xr, j in V1_S0_MISMATCHES]
    systems += [('new', rng.randrange(1, 2 ** N_BITS), t % N_BITS) for t in range(count)]
    multi = [('multi', int(x), int(jj)) for x, jj, _ in
             json.load(open(os.path.join(MYDIR, 'diagnosis', 'multi_systems.json')))['systems']]
    systems += multi
    stats = {'systems': 0, 'v1_systems': len(V1_S0_MISMATCHES), 'new_systems': count, 'multi_systems': len(multi),
             'set_equal': 0, 'order_equal': 0, 'third_checked': 0, 'third_equal': 0, 'bruteforce_equal': 0,
             'nonempty_sage': 0, 'nonempty_native': 0, 'nonempty_third': 0, 'multi': 0, 'order_equal_multi': 0}
    detail = []
    for src, xr_int, j in systems:
        xR = fld.F.from_integer(xr_int)
        assert enc(xR) == xr_int
        ref = sage_variety(fld, j, xR, fld.F(1))
        mine = nat.solve(xr_int, j)
        bf = nat.bruteforce(xr_int, j)
        th = third_sage(fld.F, xR, j) if src != 'multi' else None
        stats['systems'] += 1
        stats['set_equal'] += int(sorted(ref) == sorted(mine))
        stats['order_equal'] += int([tuple(map(int, x)) for x in ref] == [tuple(x) for x in mine])
        if th is not None:
            stats['third_checked'] += 1
            stats['third_equal'] += int(sorted(th) == sorted(mine))
        stats['bruteforce_equal'] += int(sorted(bf) == sorted(mine))
        stats['nonempty_sage'] += int(bool(ref))
        stats['nonempty_native'] += int(bool(mine))
        stats['nonempty_third'] += int(bool(th))
        if len(ref) > 1:
            stats['multi'] += 1
            stats['order_equal_multi'] += int(ref == mine)
        detail.append({'src': src, 'xR': xr_int, 'j': j, 'sage': ref, 'native': mine, 'bruteforce': bf, 'third': th})
    n = stats['systems']
    stats['ok'] = n == count + len(V1_S0_MISMATCHES) + len(multi) and \
        stats['set_equal'] == stats['order_equal'] == stats['bruteforce_equal'] == n and \
        stats['third_equal'] == stats['third_checked'] == count + len(V1_S0_MISMATCHES)
    stats['detail'] = detail
    return stats


def main():
    a = sys.argv[1:]
    opt = lambda k, d=None: a[a.index(k) + 1] if k in a else d
    arm, out, lib = opt('--arm'), opt('--out'), opt('--lib')
    lib = os.path.abspath(lib) if lib else None
    row = {'arm': arm, 'point': opt('--point'), 'pid': os.getpid(),
           'affinity': sorted(os.sched_getaffinity(0)),
           'process_time_resolution_s': time.get_clock_info('process_time').resolution,
           'load_wall_s': T_LOADED - T_PROC0,
           'native_sha256': sha256_file(lib) if lib and os.path.exists(lib) else None}
    if arm in ('B', 'N', 'Naa', 'NX'):
        s = int(opt('--scalar'))
        row.update({'scalar': s, 'rng_seed': opt('--rng-seed')})
        row.update(ic_row(arm, s, opt('--rng-seed'), lib))
    elif arm == 'rho':
        s = int(opt('--scalar'))
        row['scalar'] = s
        row.update(rho_row(s))
    elif arm == 'O':
        row.update(archived_row(lib))
        row['correct'] = row['all_equal']
    elif arm == 'selftest':
        row.update(selftest_row(lib))
        row['correct'] = row['ok']
    else:
        raise SystemExit('unknown arm %r' % arm)
    if arm in ('N', 'Naa', 'NX', 'O', 'selftest'):
        row['binding_check'] = binding_check(lib)      # after every interval of the row
        row['correct'] = bool(row.get('correct')) and row['binding_check']['ok']
    with open(out, 'w') as f:
        json.dump(row, f, default=jplain)
        f.write('\n')
    print(json.dumps({k: row.get(k) for k in ('arm', 'point', 'correct', 'cold_cpu_s', 'cpu_s')}, default=jplain),
          flush=True)
    if not row.get('correct'):
        raise SystemExit(3)


main()
