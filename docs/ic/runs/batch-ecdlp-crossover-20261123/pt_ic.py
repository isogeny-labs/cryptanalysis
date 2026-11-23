#!/usr/bin/env python3
"""Pair-table batch index calculus (the `mitm` / `mitm-prime-batched` pair-table family) in the
`ca-ic prime` abstract-op unit, executed, every recovered log checked [d]G == Q.
Counts: one per walk step / table entry / hit verification; scalar mult = ceil(3 bits(r)/2); jump table = 32 smul.
Setup charge = N(2N+1) (the count ic bench reports for the scalar table build), or N^2 with --sym."""
import sys, os, json, math, random, csv, argparse, time
sys.path.insert(0, '/home/user/workspace/docs/notes/graph-theory-ic-20261121/followups/next/batchrho')
from batch_rho import Curve, load_ic, derive_rng

class UF:
    def __init__(s, n, r):
        s.par = list(range(n)); s.u = [1]*n; s.w = [0]*n; s.pin = {}; s.r = r; s.ndet = 0; s.size = [1]*n
        s.n = n; s.bad = 0
    def find(s, v):
        path = []
        while s.par[v] != v: path.append(v); v = s.par[v]
        root = v
        # compress: compose along path from the top
        U, W = 1, 0
        for x in reversed(path):
            # l_x = u_x l_par + w_x, and par now resolved to (U,W) wrt root
            U, W = (s.u[x]*U), (s.u[x]*W + s.w[x]) % s.r
            s.par[x] = root; s.u[x] = U; s.w[x] = W
        return root
    def val(s, v):
        r = s.find(v)
        if r in s.pin:
            return (s.u[v]*s.pin[r] + s.w[v]) % s.r if v != r else s.pin[r]
        return None
    def uw(s, v):
        r = s.find(v)
        return (r, 1, 0) if v == r else (r, s.u[v], s.w[v])
    def add(s, i, j, al, be, rho):
        """al*l_i + be*l_j = rho (al,be = +-1)."""
        r = s.r
        ri, Ui, Wi = s.uw(i); rj, Uj, Wj = s.uw(j)
        if ri != rj:
            u = (-al*be*Ui*Uj); w = (be*Uj*(rho - al*Wi - be*Wj)) % r   # l_rj = u l_ri + w
            # attach smaller to larger
            if s.size[ri] >= s.size[rj]:
                s.par[rj] = ri; s.u[rj] = u; s.w[rj] = w; s.size[ri] += s.size[rj]
                if rj in s.pin:
                    pv = (s.pin.pop(rj) - w) * u % r   # l_ri = u(l_rj - w)
                    if ri in s.pin: s.bad += (s.pin[ri] != pv)
                    else: s.pin[ri] = pv
            else:
                ui = u; wi = (-u*w) % r                  # l_ri = u(l_rj - w)
                s.par[ri] = rj; s.u[ri] = ui; s.w[ri] = wi; s.size[rj] += s.size[ri]
                if ri in s.pin:
                    pv = (s.pin.pop(ri) - wi) * ui % r
                    if rj in s.pin: s.bad += (s.pin[rj] != pv)
                    else: s.pin[rj] = pv
        else:
            coef = (al*Ui + be*Uj); rhs = (rho - al*Wi - be*Wj) % r
            if coef == 0:
                if rhs != 0: s.bad += 1
            else:
                pv = rhs * pow(coef % r, -1, r) % r
                if ri in s.pin: s.bad += (s.pin[ri] != pv)
                else: s.pin[ri] = pv
    def ndetermined(s):
        return sum(s.size[r] for r in s.pin if s.par[r] == r)

def sqrt_mod(a, p):
    if a % p == 0: return 0
    if pow(a, (p-1)//2, p) != 1: return None
    if p % 4 == 3: return pow(a, (p+1)//4, p)
    # tonelli-shanks
    q, s = p-1, 0
    while q % 2 == 0: q //= 2; s += 1
    z = 2
    while pow(z, (p-1)//2, p) != p-1: z += 1
    m, c, t, R = s, pow(z, q, p), pow(a, q, p), pow(a, (q+1)//2, p)
    while t != 1:
        i, tt = 0, t
        while tt != 1: tt = tt*tt % p; i += 1
        b = pow(c, 1 << (m-i-1), p); m = i; c = b*b % p; t = t*c % p; R = R*b % p
    return R

def run(path, B, seed, K, N, fstop, start, rep, sym=False, max_steps_cap=None):
    d, cv, targets, planted = load_ic(path)
    p, r = cv.p, cv.r
    rng = derive_rng('pt', B, seed, K, N, fstop, start, rep)
    smul = cv.smul_ops
    ops = {'table': 0, 'jumps': 32*smul, 'rel_steps': 0, 'rel_seed': 0, 'desc_steps': 0, 'desc_seed': 0}
    # factor base: N smallest abscissae with a point
    FB = []; x = 1
    while len(FB) < N:
        x += 1
        rhs = (x**3 + cv.a*x + cv.b) % p
        y = sqrt_mod(rhs, p)
        if y is not None and (x, y) != None: FB.append((x, y))
    ops['table'] = (N*N if sym else N*(2*N+1))
    # table: x -> (i, si, j, sj, point)
    tab = {}
    def neg(P): return (P[0], (-P[1]) % p)
    for i in range(N):
        P = FB[i]
        D = cv.add(P, P)
        if D is not None: tab.setdefault(D[0], (i, 1, i, 1, D))
        for j in range(i+1, N):
            S = cv.add(P, FB[j]); T = cv.add(P, neg(FB[j]))
            if S is not None: tab.setdefault(S[0], (i, 1, j, 1, S))
            if T is not None: tab.setdefault(T[0], (i, 1, j, -1, T))
    # jumps
    M1 = 0x9E3779B97F4A7C15
    jc = [rng.randrange(1, r) for _ in range(32)]
    jp = [cv.mul(c, cv.G) for c in jc]
    def jidx(Pt): return ((Pt[0]*M1) & ((1 << 64)-1)) >> 59
    uf = UF(N, r)
    # relations
    nrel = 0
    WALKCAP = max(50, int(0.5*math.sqrt(r)))
    def decode(R):
        e = tab.get(R[0])
        if e is None: return None
        i, si, j, sj, T = e
        eps = 1 if R[1] == T[1] else -1       # R = eps * T (same abscissa)
        return i, eps*si, j, eps*sj
    a = 0; R = None
    steps_since = 0
    relcap = 40 * N * 20
    while uf.ndetermined() < fstop*N:
        if R is None or steps_since > WALKCAP:
            a = rng.randrange(1, r); R = cv.mul(a, cv.G); ops['rel_seed'] += smul; steps_since = 0
            if R is None: continue
        j = jidx(R)
        R = cv.add(R, jp[j]); a = (a + jc[j]) % r; ops['rel_steps'] += 1; steps_since += 1
        if R is None: R = None; continue
        dd = decode(R)
        if dd is not None:
            ops['rel_steps'] += 1  # hit verification (one counted add)
            i, al, jj, be = dd
            uf.add(i, jj, al, be, a)
            nrel += 1
        if ops['rel_steps'] > 5e7: break
    det_frac = uf.ndetermined()/N
    # descents
    verified = 0; hits_wasted = 0
    for t in range(K):
        Q = targets[t]; ok = False
        first = True
        while not ok:
            if start == 'cheap' and first:
                a = 0; b = 1; R = Q
            elif start == 'cheap':
                a = rng.randrange(1, r); b = 1; R = cv.add(cv.mul(a, cv.G), Q); ops['desc_seed'] += smul+1
            else:
                a = rng.randrange(1, r); b = rng.randrange(1, r)
                R = cv.add(cv.mul(a, cv.G), cv.mul(b, Q)); ops['desc_seed'] += 2*smul+1
            first = False
            if R is None: continue
            cap = WALKCAP
            for _ in range(cap):
                dd = decode(R)
                if dd is not None:
                    ops['desc_steps'] += 1
                    i, al, jj, be = dd
                    vi, vj = uf.val(i), uf.val(jj)
                    if vi is not None and vj is not None:
                        rhs = (al*vi + be*vj - a) % r
                        q = rhs * pow(b, -1, r) % r
                        if cv.mul(q, cv.G) == Q:
                            ok = True; verified += 1; break
                        else:
                            uf.bad += 1
                    else: hits_wasted += 1
                j = jidx(R)
                R = cv.add(R, jp[j]); a = (a + jc[j]) % r; ops['desc_steps'] += 1
                if R is None: break
    total = sum(ops.values())
    return dict(B=B, seed=seed, r=r, K=K, N=N, fstop=fstop, start=start, rep=rep, sym=int(sym), ops=total,
                ops_per_target=total/K, **{('op_'+k): v for k, v in ops.items()}, relations=nrel,
                det_frac=round(det_frac, 4), verified=verified, bad=uf.bad, hits_wasted=hits_wasted,
                status='complete' if verified == K and uf.bad == 0 else 'FAIL')

if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--ic'); ap.add_argument('--B', type=int); ap.add_argument('--seed', type=int)
    ap.add_argument('--K', type=int); ap.add_argument('--N', type=int); ap.add_argument('--fstop', type=float, default=0.95)
    ap.add_argument('--start', default='full'); ap.add_argument('--rep', type=int, default=0)
    ap.add_argument('--sym', action='store_true')
    a = ap.parse_args()
    t0 = time.time()
    print(json.dumps(run(a.ic, a.B, a.seed, a.K, a.N, a.fstop, a.start, a.rep, a.sym)), 'wall', round(time.time()-t0, 2))
