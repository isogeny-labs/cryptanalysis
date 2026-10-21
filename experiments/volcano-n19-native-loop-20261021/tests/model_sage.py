"""Pure-Python model of tau.sage's TauCurve / generator / tauDlp (no Sage), for local tests only.

It follows tau.sage line by line with rho_frob.py's PyBackend arithmetic (validated against
Sage by that experiment's selftest), Sage's lift_x choice (the smaller y; see
native/src/curve.rs), the v3 per-shift solve through ctypes (`tau6_solve`, exported by
libtau6loop.so from the v3 source), and an independent pure-Python reduced-echelon left
kernel. It is NOT the oracle of the run (Sage is: the planted arm N2X and the smoke job);
it lets the comparison code and the native trace be tested where Sage is absent.
"""
import ctypes
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
EXP = os.path.dirname(HERE)
V3 = os.path.join(EXP, '..', 'volcano-n19-native-tau6-v3-20261020')
RHO = os.path.join(EXP, '..', 'volcano-ic', 'rho-arm-20261014')
sys.path.insert(0, RHO)
import rho_frob as rf  # noqa: E402
import importlib.util  # noqa: E402

_spec = importlib.util.spec_from_file_location('v3_native_binding', os.path.join(V3, 'native_binding.py'))
nb = importlib.util.module_from_spec(_spec)  # v3's binding, by path (V3 is never put on sys.path)
_spec.loader.exec_module(nb)

N, K, P_ORD, H = 19, 6, 130873, 4
B = rf.PyBackend()
MOD = rf.MODULUS_INT


def lift_x_sage(x):
    pts = B.lift_x_all(x)
    return sorted(pts, key=lambda pt: pt[1])


class Cur:
    def __init__(self, lib):
        base = {}
        for c in range(1, 2 ** K):
            x = c
            rhs = x ^ rf.gf_inv(rf.gf_sq(x))
            if rf.gf_trace(rhs) == 0:
                base[x] = (x, rf.gf_mul(x, rf.gf_half_trace(rhs)))
        orb = lambda x: [B.frob((x, 0), e)[0] for e in range(N)]
        self.reps, self.repOf = [], {}
        for x in sorted(base):
            rx = min(orb(x))
            if rx not in self.repOf:
                self.repOf[rx] = len(self.reps)
                self.reps.append(lift_x_sage(rx)[0])
        self.base = {}
        for x, Pt in base.items():
            col = self.repOf[min(orb(x))]
            for e in range(N):
                T = B.frob(self.reps[col], e)
                if T == Pt:
                    self.base[x] = (Pt, col, e, 1)
                    break
                if T == B.neg(Pt):
                    self.base[x] = (Pt, col, e, -1)
                    break
        self.native = nb.Native(lib, N, MOD, K)
        self.enc = lambda e: e
        self.p, self.h = P_ORD, H


def generator():
    import random
    rng = random.Random('gen:E0')
    while True:
        x = rng.randrange(1, 2 ** N)
        pts = lift_x_sage(x)
        if pts:
            P = B.mul(H, pts[0])
            if P is not None:
                return P


def tau_eigen(P):
    for lam in range(P_ORD):
        if (lam * lam + lam + 2) % P_ORD == 0 and B.mul(lam, P) == B.frob(P, 1):
            return lam
    raise ValueError


def tau_relation(cur, R, stats, shifts):
    xr = R[0]
    for j in shifts:
        sols = cur.native.solve(xr, j)
        stats['gb_calls'] += 1
        for ub, wb in sols:
            if ub not in cur.base or wb not in cur.base:
                stats['spurious'] += 1
                continue
            P1, col1, e1, sg1 = cur.base[ub]
            P2, col2, e2, sg2 = cur.base[wb]
            T2 = B.frob(P2, j)
            for s1 in (1, -1):
                for s2 in (1, -1):
                    if B.add(B.mul(s1, P1), B.mul(s2, T2)) == R:
                        return [(col1, s1 * sg1, e1), (col2, s2 * sg2, (j + e2) % N)]
            stats['spurious'] += 1
    return None


def rref(rows, ncols, p):
    a = [list(r) for r in rows]
    piv, r = [], 0
    for c in range(ncols):
        sel = next((i for i in range(r, len(a)) if a[i][c] % p), None)
        if sel is None:
            continue
        a[r], a[sel] = a[sel], a[r]
        inv = pow(a[r][c], p - 2, p)
        a[r] = [x * inv % p for x in a[r]]
        for i in range(len(a)):
            if i != r and a[i][c]:
                f = a[i][c]
                a[i] = [(x - f * y) % p for x, y in zip(a[i], a[r])]
        piv.append(c)
        r += 1
        if r == len(a):
            break
    return a[:len(piv)], piv


def left_kernel_basis(M, ncols, p):
    """The reduced echelon basis of {v : v M = 0}: solve M^T v = 0, then echelonize."""
    m = len(M)
    T = [[M[i][j] for i in range(m)] for j in range(ncols)]
    R, piv = rref(T, m, p) if T else ([], [])
    free = [c for c in range(m) if c not in piv]
    vecs = []
    for f in free:
        v = [0] * m
        v[f] = 1
        for row, pc in zip(R, piv):
            v[pc] = (-row[f]) % p
        vecs.append(v)
    E, _ = rref(vecs, m, p) if vecs else ([], [])
    return E


def tau_dlp(cur, P, Q, rng, relation, extra=10):
    p, h = cur.p, cur.h
    lam = tau_eigen(P)
    stats = {'gb_calls': 0, 'spurious': 0, 'targets': 0}
    rows, rhs = [], []
    shifts = list(range(N))
    while len(rows) < len(cur.reps) + extra:
        stats['targets'] += 1
        al, be = rng.randrange(1, p), rng.randrange(1, p)
        R = B.add(B.mul(al, P), B.mul(be, Q))
        if R is None:
            continue
        rng.shuffle(shifts)
        rel = relation(cur, R, stats, shifts)
        if rel is None:
            continue
        row = {}
        for col, sign, e in rel:
            row[col] = (row.get(col, 0) + sign * pow(lam, e, p)) % p
        rows.append(row)
        rhs.append((h * al % p, h * be % p))
    used = sorted({c for r in rows for c in r})
    M = [[r.get(c, 0) for c in used] for r in rows]
    basis = left_kernel_basis(M, len(used), p)
    s = kidx = None
    for bi, v in enumerate(basis):
        A = sum(v[i] * rhs[i][0] for i in range(len(rows))) % p
        Bc = sum(v[i] * rhs[i][1] for i in range(len(rows))) % p
        if Bc:
            s, kidx = (-A * pow(Bc, p - 2, p)) % p, bi
            break
    stats.update({'relations': len(rows), 'log': s, 'recovered': s is not None and B.mul(s, P) == Q,
                  'basis': basis, 'kernel_index': kidx, 'used': used, 'lambda': lam})
    return stats


def native_trace(lib_path, scalar, seed):
    import json
    lib = ctypes.CDLL(lib_path)
    lib.tau6loop_dlp_trace.restype = ctypes.c_int64
    lib.tau6loop_dlp_trace.argtypes = [ctypes.c_uint64, ctypes.c_char_p, ctypes.c_size_t, ctypes.c_char_p,
                                       ctypes.c_size_t]
    sb = seed.encode()
    cap = 1 << 22
    buf = ctypes.create_string_buffer(cap)
    n = lib.tau6loop_dlp_trace(scalar, sb, len(sb), buf, cap)
    assert 0 <= n <= cap
    return json.loads(buf.raw[:n].decode())
