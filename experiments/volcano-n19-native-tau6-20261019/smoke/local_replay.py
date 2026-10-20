"""Local diagnostic (no Sage): replay tau.sage's tauDlp in pure Python with the
native per-relation solve, and check it against the archived Sage run.

    python3 local_replay.py --lib PATH/libtau6native.so [--instances 0-9] [--out FILE]
                            [--crosscheck N]

For each archived scalar of volcano-ic/rho-arm-20261014 (run 38520305068) it
redoes tauDlp's control flow exactly (random.Random('tau:tau6:%d'), the
randrange / shuffle sequence, the shift loop, the base and point checks),
using ../native through ctypes for the variety of each shift system, and
compares targets, gb_calls, spurious, relations and the recovered log with
results/arms.jsonl. With --crosscheck N it also compares the native variety
with an independent pure-Python evaluation of S3 on all 4096 (u, w) for the
first N systems. Pure-Python point arithmetic is rho_frob.py's PyBackend
(validated against Sage by that experiment's selftest).
"""
import argparse
import ctypes
import json
import os
import random
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
RHO = os.path.join(HERE, '..', '..', 'volcano-ic', 'rho-arm-20261014')
sys.path.insert(0, RHO)
import rho_frob as rf  # noqa: E402

N, K, P_ORD, H = 19, 6, 130873, 4
MOD = rf.MODULUS_INT
B = rf.PyBackend()


def parse_z(s):
    v = 0
    for t in s.replace(' ', '').split('+'):
        if t == '1':
            v |= 1
        elif t == 'z':
            v |= 2
        else:
            v |= 1 << int(t.split('^')[1])
    return v


class Native:
    def __init__(self, path):
        self.lib = ctypes.CDLL(path)
        self.lib.tau6_new.restype = ctypes.c_void_p
        self.lib.tau6_new.argtypes = [ctypes.c_uint64, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_uint64]
        for f in (self.lib.tau6_solve, self.lib.tau6_solve_bruteforce):
            f.restype = ctypes.c_int64
            f.argtypes = [ctypes.c_void_p, ctypes.c_uint64, ctypes.c_uint32,
                          ctypes.POINTER(ctypes.c_uint32), ctypes.c_uint32]
        self.ctx = self.lib.tau6_new(MOD, N, K, 1)
        assert self.ctx
        self.buf = (ctypes.c_uint32 * 4096)()

    def solve(self, xr, j):
        c = self.lib.tau6_solve(self.ctx, xr, j, self.buf, 4096)
        assert c >= 0
        return [(self.buf[i] & 63, self.buf[i] >> 6) for i in range(c)]


def s3_python(xr, j):
    out = []
    xr2 = rf.gf_sq(xr)
    for u in range(64):
        for w in range(64):
            x2 = w
            for _ in range(j):
                x2 = rf.gf_sq(x2)
            m = rf.gf_mul(u, x2)
            f = rf.gf_sq(m) ^ rf.gf_mul(xr2, rf.gf_sq(u) ^ rf.gf_sq(x2)) ^ rf.gf_mul(xr, m) ^ 1
            if f == 0:
                out.append((u, w))
    return out


def build_base():
    base = {}
    for c in range(1, 64):
        x = c
        rhs = x ^ rf.gf_inv(rf.gf_sq(x))
        if rf.gf_trace(rhs) == 0:
            base[x] = (x, rf.gf_mul(x, rf.gf_half_trace(rhs)))
    reps, repOf = [], {}
    orb = lambda x: [B.frob((x, 0), e)[0] for e in range(N)]
    for x in sorted(base):
        rx = min(orb(x))
        if rx not in repOf:
            repOf[rx] = len(reps)
            reps.append(B.lift_x_all(rx)[0])
    table = {}
    for x, Pt in base.items():
        rx = min(orb(x))
        col = repOf[rx]
        for e in range(N):
            T = B.frob(reps[col], e)
            if T == Pt:
                table[x] = (Pt, col, e, 1)
                break
            if T == B.neg(Pt):
                table[x] = (Pt, col, e, -1)
                break
        assert x in table
    return table, reps


def kernel_log(rows, rhs, p):
    used = sorted({c for r in rows for c in r})
    idx = {c: i for i, c in enumerate(used)}
    m, ncol = len(rows), len(used)
    M = [[0] * ncol + [1 if i == t else 0 for t in range(m)] for i in range(m)]
    for i, r in enumerate(rows):
        for c, v in r.items():
            M[i][idx[c]] = (M[i][idx[c]] + v) % p
    piv = 0
    for col in range(ncol):
        sel = next((i for i in range(piv, m) if M[i][col]), None)
        if sel is None:
            continue
        M[piv], M[sel] = M[sel], M[piv]
        inv = pow(M[piv][col], p - 2, p)
        M[piv] = [x * inv % p for x in M[piv]]
        for i in range(m):
            if i != piv and M[i][col]:
                f = M[i][col]
                M[i] = [(a - f * b) % p for a, b in zip(M[i], M[piv])]
        piv += 1
    for i in range(piv, m):
        v = M[i][ncol:]
        A = sum(v[t] * rhs[t][0] for t in range(m)) % p
        Bc = sum(v[t] * rhs[t][1] for t in range(m)) % p
        if Bc:
            return (-A * pow(Bc, p - 2, p)) % p
    return None


def tau_dlp(nat, P, Q, lam, rng, table, ncol, extra=10, cross=None, relog=None):
    p = P_ORD
    st = {'gb_calls': 0, 'spurious': 0, 'targets': 0, 'nonempty_calls': 0, 'multi_solution_calls': 0,
          'multi_valid_calls': 0}
    rows, rhs = [], []
    shifts = list(range(N))
    t0 = time.process_time()
    while len(rows) < ncol + extra:
        st['targets'] += 1
        al, be = rng.randrange(1, int(p)), rng.randrange(1, int(p))
        R = B.add(B.mul(al, P), B.mul(be, Q))
        if R is None:
            continue
        rng.shuffle(shifts)
        rel = None
        for j in shifts:
            st['gb_calls'] += 1
            sols = nat.solve(R[0], j)
            if cross is not None and cross[0] > 0:
                cross[0] -= 1
                ref = s3_python(R[0], j)
                assert ref == sols, ('native != python S3', R[0], j)
                cross[1] += 1
            if sols:
                st['nonempty_calls'] += 1
            if len(sols) > 1:
                st['multi_solution_calls'] += 1
            valid = 0
            found = None
            for (x1, x2) in sols:
                if x1 not in table or x2 not in table:
                    st['spurious'] += 1 if found is None else 0
                    continue
                P1, c1, e1, g1 = table[x1]
                P2, c2, e2, g2 = table[x2]
                T2 = B.frob(P2, j)
                hit = None
                for s1 in (1, -1):
                    for s2 in (1, -1):
                        if hit is None and B.add(B.mul(s1, P1), B.mul(s2, T2)) == R:
                            hit = [(c1, s1 * g1, e1), (c2, s2 * g2, (j + e2) % N)]
                if hit is not None:
                    valid += 1
                    if found is None:
                        found = hit
                elif found is None:
                    st['spurious'] += 1
            if valid > 1:
                st['multi_valid_calls'] += 1
            if found is not None:
                rel = found
                break
        if rel is None:
            continue
        row = {}
        for col, sign, e in rel:
            row[col] = (row.get(col, 0) + sign * pow(lam, e, p)) % p
        rows.append(row)
        rhs.append((H * al % p, H * be % p))
        if relog is not None:
            relog.append(rel)
    t1 = time.process_time()
    s = kernel_log(rows, rhs, p)
    st.update({'relations': len(rows), 'relation_cpu_s_local': t1 - t0,
               'total_cpu_s_local': time.process_time() - t0, 'log': s,
               'recovered': s is not None and B.mul(s, P) == Q})
    return st


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--lib', required=True)
    ap.add_argument('--instances', default='0-9')
    ap.add_argument('--crosscheck', type=int, default=0)
    ap.add_argument('--out')
    a = ap.parse_args()
    lo, hi = map(int, a.instances.split('-'))
    info = json.load(open(os.path.join(RHO, 'results', 'runtime-info.json')))
    P = (parse_z(info['P'][0]), parse_z(info['P'][1]))
    lam = int(info['lambda'])
    assert B.on_curve(P) and B.mul(P_ORD, P) is None and B.mul(lam, P) == B.frob(P, 1)
    arch = {r['instance']: r for r in map(json.loads, open(os.path.join(RHO, 'results', 'arms.jsonl')))
            if r['arm'] == 'tau6'}
    proto = json.load(open(os.path.join(RHO, 'protocol.json')))
    table, reps = build_base()
    nat = Native(a.lib)
    cross = [a.crosscheck, 0]
    out = []
    for ii in range(lo, hi + 1):
        s = proto['scalars'][ii]
        Q = B.mul(s, P)
        st = tau_dlp(nat, P, Q, lam, random.Random(proto['arms']['tau6']['rng_seed'] % ii), table, len(reps),
                     cross=cross)
        ar = arch[ii]
        cmp = {f: (st[f], ar[f]) for f in ('targets', 'gb_calls', 'spurious', 'relations')}
        cmp['log'] = (st['log'], ar['log'])
        st['instance'], st['scalar'] = ii, s
        st['archived_sage_cpu_s'] = ar['total_cpu_s']
        st['equal_to_archive'] = all(x == y for x, y in cmp.values())
        st['compare'] = cmp
        out.append(st)
        print(json.dumps(st), flush=True)
    res = {'kind': 'local diagnostic (cloud-agent VM, pure-Python driver + native solve); not timing evidence',
           'orbits': len(reps), 'v_points': len(table), 'crosschecked_systems': cross[1],
           'all_equal_to_archive': all(r['equal_to_archive'] for r in out), 'instances': out}
    if a.out:
        json.dump(res, open(a.out, 'w'), indent=1)
    print(json.dumps({k: v for k, v in res.items() if k != 'instances'}))


if __name__ == '__main__':
    main()
