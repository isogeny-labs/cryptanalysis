#!/usr/bin/env python3
"""Lift-success sweep for prime-field xedni over toy primes (see PROTOCOL.md).

One trial = one random instance (curve E/F_p, base point P, secret l, r points
m_i*P and Q=l*P), one certified lift (ca-icx xedni-lift: LLL + exact Babai +
bounded exact discriminant search), and one bounded exact search for an
integer relation among the r lifted rational points.  Every reported success
is verified over Q with exact rational arithmetic, and reduced mod p.
Standard library only.
"""
from __future__ import annotations
import argparse, hashlib, json, math, os, random, subprocess, sys, tempfile, time
from fractions import Fraction
from multiprocessing import Pool

NBOX = 6                     # relation box |n_i| <= NBOX (frozen)
RADIUS = 1                   # neighbourhood radius (frozen)
Q_PRIMES = (2**61 - 1, 2**89 - 1, 2**107 - 1)
POOL = 40                    # curves per (p, family)
BIN = None


# ---------------------------------------------------------------- F_p curves
def legendre_table(p):
    sq = {}
    for y in range(p):
        sq.setdefault(y * y % p, []).append(y)
    return sq


def ec_add_p(P, Q, a, p):
    if P is None: return Q
    if Q is None: return P
    x1, y1 = P; x2, y2 = Q
    if x1 == x2:
        if (y1 + y2) % p == 0: return None
        lam = (3 * x1 * x1 + a) * pow(2 * y1, -1, p) % p
    else:
        lam = (y2 - y1) * pow(x2 - x1, -1, p) % p
    x3 = (lam * lam - x1 - x2) % p
    return (x3, (lam * (x1 - x3) - y1) % p)


def ec_mul_p(k, P, a, p):
    R = None
    while k:
        if k & 1: R = ec_add_p(R, P, a, p)
        P = ec_add_p(P, P, a, p); k >>= 1
    return R


def curve_pool(p, family, rng):
    """Return list of (a, b, N, sqtable) with nonzero discriminant."""
    sq = legendre_table(p)
    out = []
    tries = 0
    while len(out) < POOL and tries < 10000:
        tries += 1
        if family == "j0":
            a, b = 0, rng.randrange(1, p)
        else:
            a, b = rng.randrange(p), rng.randrange(1, p)
        if (4 * a**3 + 27 * b * b) % p == 0: continue
        N = 1
        for x in range(p):
            N += len(sq.get((x**3 + a * x + b) % p, []))
        out.append((a, b, N))
    return out, sq


def divisors_order(N, P, a, p):
    n = N
    for f in _prime_factors(N):
        while n % f == 0 and ec_mul_p(n // f, P, a, p) is None: n //= f
    return n


def _prime_factors(n):
    fs, f = [], 2
    while f * f <= n:
        if n % f == 0:
            fs.append(f)
            while n % f == 0: n //= f
        f += 1
    if n > 1: fs.append(n)
    return fs


# ----------------------------------------------------------- integer algebra
def col_hnf_kernel(B, ncols):
    """Column operations: returns (H, U) with B*U = H lower-echelon, U unimodular."""
    m = len(B)
    H = [row[:] for row in B]
    U = [[int(i == j) for j in range(ncols)] for i in range(ncols)]
    piv = []
    c = 0
    for r in range(m):
        if c >= ncols: break
        # gcd-reduce columns c..ncols-1 on row r
        while True:
            nz = [j for j in range(c, ncols) if H[r][j] != 0]
            if len(nz) <= 1: break
            jm = min(nz, key=lambda j: abs(H[r][j]))
            for j in nz:
                if j == jm: continue
                q = H[r][j] // H[r][jm]
                for i in range(m): H[i][j] -= q * H[i][jm]
                for i in range(ncols): U[i][j] -= q * U[i][jm]
        nz = [j for j in range(c, ncols) if H[r][j] != 0]
        if not nz: continue
        j = nz[0]
        if j != c:
            for i in range(m): H[i][c], H[i][j] = H[i][j], H[i][c]
            for i in range(ncols): U[i][c], U[i][j] = U[i][j], U[i][c]
        piv.append(r); c += 1
    return H, U, piv


def solve_affine(B, rhs, ncols):
    """Integer w with B w = rhs, and an integer kernel basis; None if unsolvable."""
    H, U, piv = col_hnf_kernel(B, ncols)
    rank = len(piv)
    y = [0] * ncols
    for k, r in enumerate(piv):
        s = rhs[r] - sum(H[r][j] * y[j] for j in range(k))
        if s % H[r][k]: return None
        y[k] = s // H[r][k]
    w = [sum(U[i][j] * y[j] for j in range(ncols)) for i in range(ncols)]
    if any(sum(B[r][i] * w[i] for i in range(ncols)) != rhs[r] for r in range(len(B))): return None
    ker = [[U[i][j] for i in range(ncols)] for j in range(rank, ncols)]
    return w, ker, rank


# --------------------------------------------------------- Weierstrass group
def w_add(P, Q, c, mod=None):
    """General Weierstrass add; c=(a1,a2,a3,a4,a6). Fraction or int mod arithmetic."""
    if P is None: return Q
    if Q is None: return P
    a1, a2, a3, a4, a6 = c
    x1, y1 = P; x2, y2 = Q
    if mod is None:
        inv = lambda t: Fraction(1) / t
        red = lambda t: t
    else:
        inv = lambda t: pow(t, -1, mod)
        red = lambda t: t % mod
    if x1 == x2:
        if red(y1 + y2 + a1 * x2 + a3) == 0: return None
        lam = red((3 * x1 * x1 + 2 * a2 * x1 + a4 - a1 * y1) * inv(red(2 * y1 + a1 * x1 + a3)))
    else:
        lam = red((y2 - y1) * inv(red(x2 - x1)))
    nu = red(y1 - lam * x1)
    x3 = red(lam * lam + a1 * lam - a2 - x1 - x2)
    y3 = red(-(lam + a1) * x3 - nu - a3)
    return (x3, y3)


def w_neg(P, c, mod=None):
    if P is None: return None
    a1, _, a3, _, _ = c
    y = -P[1] - a1 * P[0] - a3
    return (P[0], y % mod if mod else y)


def w_mul(k, P, c, mod=None):
    if k < 0: return w_mul(-k, w_neg(P, c, mod), c, mod)
    R = None
    while k:
        if k & 1: R = w_add(R, P, c, mod)
        P = w_add(P, P, c, mod); k >>= 1
    return R


def w_disc(c):
    a1, a2, a3, a4, a6 = c
    b2 = a1 * a1 + 4 * a2; b4 = 2 * a4 + a1 * a3; b6 = a3 * a3 + 4 * a6
    b8 = a1 * a1 * a6 + 4 * a2 * a6 - a1 * a3 * a4 + a2 * a3 * a3 - a4 * a4
    return -b2 * b2 * b8 - 8 * b4**3 - 27 * b6 * b6 + 9 * b2 * b4 * b6


def on_curve(P, c):
    a1, a2, a3, a4, a6 = c
    x, y = P
    return y * y + a1 * x * y + a3 * y == x**3 + a2 * x * x + a4 * x + a6


def fp_relation_exists(ms, n, N):
    """Is there 0 != v in [-N,N]^r with sum v_i m_i = 0 mod n (relation among the F_p points)?"""
    r = len(ms); h = (r + 1) // 2

    def enum(idx):
        acc = [((), 0)]
        for i in idx:
            acc = [(v + (k,), (S + k * ms[i]) % n) for v, S in acc for k in range(-N, N + 1)]
        return acc
    left = {}
    for v, S in enum(range(h)): left.setdefault(S, []).append(v)
    for v, S in enum(range(h, r)):
        for vl in left.get((-S) % n, ()):
            if any(vl + v): return True
    return False


def find_relation(pts, c, N):
    """Bounded search for 0 != n in [-N,N]^r with sum n_i P_i = O over Q.
    Mod-q meet-in-the-middle, every hit verified exactly over Q.
    Returns (n, verified) or (None, False)."""
    r = len(pts)
    D = w_disc(c)
    q = next(q for q in Q_PRIMES if D % q != 0)
    cq = tuple(t % q for t in c)
    pq = [(x % q, y % q) for x, y in pts]
    tabs = []
    for P in pq:
        t = {0: None}
        cur = None
        for n in range(1, N + 1):
            cur = w_add(cur, P, cq, q); t[n] = cur; t[-n] = w_neg(cur, cq, q)
        tabs.append(t)
    h = (r + 1) // 2

    def enum(idx):
        acc = [((), None)]
        for i in idx:
            new = []
            for n, S in acc:
                for k in range(-N, N + 1):
                    new.append((n + (k,), w_add(S, tabs[i][k], cq, q)))
            acc = new
        return acc
    L = enum(range(h)); R = enum(range(h, r))
    left = {}
    for n, S in L: left.setdefault(S, []).append(n)
    cands = []
    for n, S in R:
        key = w_neg(S, cq, q)
        for nl in left.get(key, ()):
            v = nl + n
            if any(v): cands.append(v)
    cands.sort(key=lambda v: (sum(map(abs, v)), v))
    for v in cands:
        S = None
        for k, P in zip(v, pts):
            S = w_add(S, w_mul(k, (Fraction(P[0]), Fraction(P[1])), c), c)
        if S is None: return v, True
    return None, False


# -------------------------------------------------------------------- trial
def run_trial(args):
    p, family, lift, r, idx, master, tmpdir = args
    key = f"{master}|{p}|{family}|{lift}|{r}|{idx}"
    rng = random.Random(key)
    cv = POOLS[(p, family)]
    (a, b, N), sq = cv[0][idx % len(cv[0])], cv[1]
    row = dict(p=p, family=family, lift=lift, r=r, idx=idx, a=a, b=b, N=N, status="", success=0)
    # base point and order
    for _ in range(200):
        x = rng.randrange(p)
        ys = sq.get((x**3 + a * x + b) % p)
        if ys: break
    else:
        row["status"] = "no_point"; return row
    P = (x, rng.choice(ys))
    n = divisors_order(N, P, a, p)
    row["ord"] = n
    if n < 2 * r + 1:
        row["status"] = "small_order"; return row
    cls = set(); ms = []
    while len(ms) < r - 1:
        m = rng.randrange(1, n)
        if m in cls or (n - m) in cls: continue
        cls.add(m); ms.append(m)
    while True:
        l = rng.randrange(1, n)
        if l not in cls and (n - l) not in cls: break
    ms.append(l)  # last point is Q = l*P
    row["fp_rel"] = int(fp_relation_exists(ms, n, NBOX))
    fp_pts = [ec_mul_p(m, P, a, p) for m in ms]
    if any(t is None for t in fp_pts):
        row["status"] = "identity"; return row
    # lifts: balanced; family 'wide' adds a random multiple of p in {-1,0,1}
    bal = lambda t: t - p if t > p // 2 else t
    pts = []
    for (x, y) in fp_pts:
        X, Y = bal(x), bal(y)
        if lift == "wide":
            X += p * rng.choice((-1, 0, 1)); Y += p * rng.choice((-1, 0, 1))
        pts.append((X, Y))
    B = [[y * y, x * y, y, x**3, x * x, x, 1] for x, y in pts]
    u0 = [1, 0, 0, -1, 0, -a, -b]
    Bu0 = [sum(r_[i] * u0[i] for i in range(7)) for r_ in B]
    if any(t % p for t in Bu0):
        row["status"] = "internal_not_on_curve"; return row
    sol = solve_affine(B, [-t // p for t in Bu0], 7)
    if sol is None:
        row["status"] = "no_integer_solution"; return row
    w0, ker, rank = sol
    if rank != r:
        row["status"] = "rank_deficient"; return row
    part = [u0[i] + p * w0[i] for i in range(7)]
    dirs = [[p * t for t in k] for k in ker]
    inp = dict(particular=[str(t) for t in part], directions=[[str(t) for t in d] for d in dirs],
               exact_constraints=[[str(t) for t in rw] for rw in B], congruence_modulus=str(p))
    fn = os.path.join(tmpdir, f"in-{os.getpid()}.json")
    with open(fn, "w") as f: json.dump(inp, f)
    cap = 3 ** len(dirs)
    cp = subprocess.run([BIN, "--json", "xedni-lift", "--input", fn, "--radius", str(RADIUS),
                         "--max-candidates", str(cap)], capture_output=True, text=True)
    if cp.returncode != 0:
        row["status"] = "lift_error"; row["err"] = (cp.stderr or cp.stdout)[-200:]; return row
    res = json.loads(cp.stdout)["result"]
    if not (res["exact_constraints_preserved"] and res["congruence_preserved"] and res["optimized_score"]["nonsingular"]):
        row["status"] = "lift_uncertified"; return row
    u = [int(t) for t in res["optimized_coefficients"]]
    a0, a1, a3, a00, a2, a4, a6 = u[0], u[1], u[2], -u[3], -u[4], -u[5], -u[6]
    c3 = a0 * a00
    c = (a1, a0 * a2, a3 * c3, a0 * a4 * c3, a0 * a6 * c3 * c3)
    W = [(c3 * x, c3 * a0 * y) for x, y in pts]
    row["coef_bits"] = res["optimized_score"]["coefficient_height_bits"]
    row["disc_bits"] = res["optimized_score"]["discriminant_bits"]
    # certificates: lift reduces to E mod p and passes through the lifted points
    ok = all(on_curve(Pt, c) for Pt in W) and w_disc(c) != 0
    ok = ok and all((c[i] - t) % p == 0 for i, t in enumerate((0, 0, 0, a, b)))
    ok = ok and all((W[i][0] - fp_pts[i][0]) % p == 0 and (W[i][1] - fp_pts[i][1]) % p == 0 for i in range(r))
    if not ok:
        row["status"] = "lift_cert_failed"; return row
    row["status"] = "ok"
    v, ver = find_relation(W, c, NBOX)
    if v is None: return row
    # certification of the relation: exact over Q (done in find_relation) + mod p
    S = None
    for k, m in zip(v, fp_pts):
        S = ec_add_p(S, ec_mul_p(k % n, m, a, p), a, p)
    # exact re-check, independent code path (integer-only projective sum is overkill; recompute)
    S2 = None
    for k, Pt in zip(v, W):
        S2 = w_add(S2, w_mul(k, (Fraction(Pt[0]), Fraction(Pt[1])), c), c)
    if not (ver and S2 is None and S is None):
        row["status"] = "relation_cert_failed"; return row
    row["success"] = 1
    row["rel"] = list(v)
    row["weight"] = sum(1 for k in v if k)
    nq = v[-1]
    row["torsion"] = int(row["weight"] == 1)
    if math.gcd(nq, n) == 1:
        lrec = (-pow(nq, -1, n) * sum(k * m for k, m in zip(v[:-1], ms))) % n
        row["dl_recovered"] = int(lrec == l % n)
    else:
        row["dl_recovered"] = 0
    return row


POOLS = {}


def selftest():
    """Positive and negative controls for the relation detector and the certificates."""
    out = []
    c = (0, 0, 0, 0, 1)                        # y^2 = x^3 + 1: torsion Z/6 = <(2,3)>
    A, T3 = (2, 3), (0, 1)
    assert all(on_curve(P, c) for P in (A, T3))
    v, ok = find_relation([A, T3], c, NBOX)
    out.append(("positive control y^2=x^3+1 [(2,3),(0,1)] relation found", v is not None and ok, v))
    S = None
    for k, P in zip(v, [A, T3]): S = w_add(S, w_mul(k, (Fraction(P[0]), Fraction(P[1])), c), c)
    out.append(("positive control exact sum is O", S is None, None))
    bad = list(v); bad[0] += 1
    S = None
    for k, P in zip(bad, [A, T3]): S = w_add(S, w_mul(k, (Fraction(P[0]), Fraction(P[1])), c), c)
    out.append(("mutated relation is rejected by the exact check", S is not None, bad))
    c2 = (0, 0, 0, 0, 17)                      # y^2 = x^3 + 17, rank 2
    pts = [(-2, 3), (-1, 4)]
    assert all(on_curve(P, c2) for P in pts)
    v, ok = find_relation(pts, c2, NBOX)
    out.append(("negative control y^2=x^3+17 [(-2,3),(-1,4)] no relation in box", v is None, v))
    out.append(("every Q_PRIME is prime", all(is_prime(q) for q in Q_PRIMES), None))
    out.append(("every sweep prime is prime", all(is_prime(q) for q in SWEEP_PRIMES), None))
    return out


def is_prime(n):
    if n < 2: return False
    for sp in (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37):
        if n % sp == 0: return n == sp
    d, s = n - 1, 0
    while d % 2 == 0: d //= 2; s += 1
    for a_ in (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37):
        x = pow(a_, d, n)
        if x in (1, n - 1): continue
        for _ in range(s - 1):
            x = x * x % n
            if x == n - 1: break
        else: return False
    return True


SWEEP_PRIMES = (31, 67, 127, 251, 509, 1021, 2039, 4093, 8191, 16381, 32749, 65521)


def init_worker(binpath, master):
    global BIN
    BIN = binpath
    for p in PRIMES:
        for fam in FAMS:
            POOLS[(p, fam)] = curve_pool(p, fam, random.Random(f"{master}|pool|{p}|{fam}"))


PRIMES = []; FAMS = ("generic", "j0")


def main():
    global PRIMES, FAMS
    if len(sys.argv) > 1 and sys.argv[1] == "selftest":
        res = selftest()
        for name, ok, extra in res: print(("PASS" if ok else "FAIL"), name, extra if extra else "")
        sys.exit(0 if all(ok for _, ok, _ in res) else 1)
    ap = argparse.ArgumentParser()
    ap.add_argument("--binary", required=True)
    ap.add_argument("--master", default="xedni-lift-success-20261112")
    ap.add_argument("--primes", required=True)
    ap.add_argument("--families", default="generic,j0")
    ap.add_argument("--lifts", default="balanced,wide")
    ap.add_argument("--rs", default="3,4,5,6")
    ap.add_argument("--trials", type=int, required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--procs", type=int, default=4)
    ap.add_argument("--chunk", type=int, default=0)
    a = ap.parse_args()
    PRIMES = [int(t) for t in a.primes.split(",")]
    FAMS = tuple(a.families.split(","))
    jobs = []
    tmp = tempfile.mkdtemp(prefix="xl-")
    for p in PRIMES:
        for fam in FAMS:
            for lift in a.lifts.split(","):
                for r in map(int, a.rs.split(",")):
                    for i in range(a.trials):
                        jobs.append((p, fam, lift, r, i, a.master, tmp))
    t0 = time.time()
    with Pool(a.procs, initializer=init_worker, initargs=(a.binary, a.master)) as pool, open(a.out, "w") as f:
        for k, row in enumerate(pool.imap_unordered(run_trial, jobs, chunksize=8)):
            f.write(json.dumps(row, sort_keys=True) + "\n")
            if k % 500 == 0:
                print(f"{k}/{len(jobs)} {time.time()-t0:.0f}s", file=sys.stderr, flush=True)
    print(f"done {len(jobs)} trials in {time.time()-t0:.1f}s", file=sys.stderr)


if __name__ == "__main__":
    main()
