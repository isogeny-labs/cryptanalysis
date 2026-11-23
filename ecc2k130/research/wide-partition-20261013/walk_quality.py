#!/usr/bin/env python3
"""Wide-partition walk-quality panel on the GF(2^23) test curve.

Measures the work-to-first-orbit-repeat of the shipping iteration function

    R' = R + sigma^j(R),    j = 3 + branch(HW(x_R))

for branch counts r = 8 (shipping, (HW>>1) mod 8), 16 and 32, against an
ideal-branch control whose selector is the orbit key itself.  Everything is
built from the client's own generated/eccF23.h tables (permuted type-II ONB,
squaring permutation, polynomial-basis images), and the fast field is
cross-checked against codegen/field.py and codegen/curves.py before any
measurement runs.

Single-walk runs: each trial walks from an independent random order-ell
point until its orbit key repeats (the rho cycle closes).  The ideal-walk
mean is sqrt(pi*M/2) with M = ell/46 x-orbits; ratios against the r=8 mean
carry the r-adding penalty of the branch count.

Outputs RECEIPT.md beside this file.

No type hints, camelCase identifiers, no itertools (project convention).
"""
import argparse
import json
import math
import random
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "codegen"))
import field as repoField          # noqa: E402
import curves as repoCurves        # noqa: E402
import cycles as repoCycles        # noqa: E402

HEADER = ROOT / "generated" / "eccF23.h"

MODPOLY = (1 << 23) | (1 << 5) | 1     # x^23 + x^5 + 1, PB_TAPS {5,-1,-1}
MASK23 = (1 << 23) - 1
LOWPOLY = (1 << 5) | 1                # x^23 == x^5 + 1


def popcount(x):
    return bin(x).count("1")



def parseHeader():
    text = HEADER.read_text()
    sq = re.search(r"SQ_PERM\[23\] = \{(.*?)\};", text, re.S).group(1)
    sqPerm = [int(v) for v in re.findall(r"\d+", sq)]
    zt = re.search(r"Z_TO_ONB\[23\]\[3\] = \{(.*?)\n\};", text, re.S).group(1)
    rows = re.findall(r"\{([^}]*)\}", zt)
    zToOnb = []
    for row in rows:
        first = re.search(r"0x([0-9a-f]+)ull", row)
        zToOnb.append(int(first.group(1), 16))
    ell = int(re.search(r'ELL_DEC = "(\d+)"', text).group(1))
    assert len(sqPerm) == 23 and len(zToOnb) == 23
    assert all(0 <= v < (1 << 23) for v in zToOnb)
    return sqPerm, zToOnb, ell


def byteTables(cols):
    """cols[i] is the image of basis bit i; three 256-entry tables apply the map.

    The third byte of a 23-bit value has only seven live bits, so the column
    list is padded to 24 for full byte lookups."""
    cols = list(cols) + [0] * (24 - len(cols)) if len(cols) < 24 else list(cols)
    tables = []
    for p in range(3):
        tab = [0] * 256
        for v in range(1, 256):
            low = v & -v
            tab[v] = tab[v ^ low] ^ cols[p * 8 + (low.bit_length() - 1)]
        tables.append(tab)
    return tables


def applyTables(tabs, x):
    return tabs[0][x & 0xFF] ^ tabs[1][(x >> 8) & 0xFF] ^ tabs[2][(x >> 16) & 0xFF]


def invertGf2(cols, m):
    """Invert an m x m GF(2) matrix given by column images.  Returns inverse columns."""
    rows = [[(cols[j] >> i) & 1 for j in range(m)] for i in range(m)]
    aug = [[rows[i][j] for j in range(m)] + [1 if i == j else 0 for j in range(m)] for i in range(m)]
    for col in range(m):
        piv = next((r for r in range(col, m) if aug[r][col]), None)
        if piv is None:
            raise ValueError("singular matrix")
        aug[col], aug[piv] = aug[piv], aug[col]
        for r in range(m):
            if r != col and aug[r][col]:
                for c in range(2 * m):
                    aug[r][c] ^= aug[col][c]
    invCols = [0] * m
    for j in range(m):
        v = 0
        for i in range(m):
            if aug[i][m + j]:
                v |= 1 << i
        invCols[j] = v
    return invCols


class FastField:
    """Poly-basis GF(2^23) with table-driven ONB conversion and sigma^j.

    The reduction modulus is derived from the repository model (z^23 expressed
    in the polynomial basis through generated/eccF23.h's tables) rather than
    assumed from PB_TAPS."""

    def __init__(self):
        self.sqPerm, self.zToOnb, self.ell = parseHeader()
        # poly -> onb23: image of poly bit k is zToOnb[k].
        self.p2oTabs = byteTables(self.zToOnb)
        # onb23 -> poly: invert the matrix whose columns are zToOnb bits.
        cols = list(self.zToOnb)
        self.o2pCols = invertGf2(cols, 23)
        self.o2pTabs = byteTables(self.o2pCols)
        # sigma on onb23 ints: input bit i -> output bit sqPerm[i].
        piCols = [1 << self.sqPerm[i] for i in range(23)]
        self.piTabs = byteTables(piCols)
        # the true modulus: z^23 in the polynomial basis
        onb = repoField.Onb(23)
        zp = onb.fromCoords(self.zToOnb[1])
        p = zp
        for _ in range(22):
            p = onb.mul(p, zp)
        w = applyTables(self.o2pTabs, onb.toCoords(p))
        assert 0 < w < (1 << 23)
        self.modPoly = (1 << 23) | w
        self.modBits = [i for i in range(23) if (w >> i) & 1]
        # sigma^j on poly ints, j = 3..34, composed through the ONB.
        self.sigmaTabs = {}
        for j in range(3, 35):
            perm = list(range(23))
            for step in range(j):
                perm = [self.sqPerm[perm[i]] for i in range(23)]
            colsj = []
            for k in range(23):
                u = self.zToOnb[k]
                v = u
                for step in range(j):
                    v = applyTables(self.piTabs, v)
                colsj.append(applyTables(self.o2pTabs, v))
            self.sigmaTabs[j] = byteTables(colsj)
        self.sqrTabs = byteTables([1 << (2 * i) for i in range(23)])

    def toOnb(self, x):
        return applyTables(self.p2oTabs, x)

    def sigma(self, j, x):
        tabs = self.sigmaTabs[j]
        return tabs[0][x & 0xFF] ^ tabs[1][(x >> 8) & 0xFF] ^ tabs[2][(x >> 16) & 0xFF]

    def reduce(self, r):
        modBits = self.modBits
        while r >> 23:
            t = r >> 23
            r = r & MASK23
            for b in modBits:
                r ^= t << b
        return r

    def mult(self, a, b):
        r = 0
        while a:
            if a & 1:
                r ^= b
            a >>= 1
            b <<= 1
        return self.reduce(r)

    def sqr(self, a):
        return self.reduce(applyTables(self.sqrTabs, a))

    def inv(self, a):
        # binary XGCD in GF(2)[x] modulo the derived modulus
        r0, r1 = self.modPoly, a
        s0, s1 = 0, 1
        while r1:
            while r0.bit_length() >= r1.bit_length() and r1:
                sh = r0.bit_length() - r1.bit_length()
                r0 ^= r1 << sh
                s0 ^= s1 << sh
            r0, r1 = r1, r0
            s0, s1 = s1, s0
        if r0 != 1:
            raise ValueError("not invertible")
        return self.reduce(s0)

    def orbitKey(self, u):
        """min over the Frobenius conjugates of the onb23 int u."""
        piTabs = self.piTabs
        best = u
        v = u
        for _ in range(22):
            v = piTabs[0][v & 0xFF] ^ piTabs[1][(v >> 8) & 0xFF] ^ piTabs[2][(v >> 16) & 0xFF]
            if v < best:
                best = v
        return best

    # ---- point arithmetic, formulas copied from codegen/curves.py Curve ----
    def pointAdd(self, p, q):
        x1, y1 = p
        x2, y2 = q
        d = x1 ^ x2
        lam = self.mult(y1 ^ y2, self.inv(d))
        x3 = self.sqr(lam) ^ lam ^ d
        y3 = self.mult(lam, x1 ^ x3) ^ x3 ^ y1
        return (x3, y3)

    def pointDbl(self, p):
        x, y = p
        lam = x ^ self.mult(y, self.inv(x))
        x3 = self.sqr(lam) ^ lam
        y3 = self.sqr(x) ^ self.mult(lam ^ 1, x3)
        return (x3, y3)

    def pointMul(self, p, k):
        r = None
        b = p
        while k:
            if k & 1:
                r = b if r is None else self.pointAdd(r, b)
            b = self.pointDbl(b)
            k >>= 1
        return r

    def branch(self, mode, r, hw, key):
        if mode == "shift":
            return (hw >> 1) % r
        if mode == "plain":
            return hw % r
        return key % r

    def walk(self, start, r, mode, maxSteps, collectBranches=False):
        """Single walk, steps until its own orbit key repeats (diagnostics only)."""
        x, y = start
        seen = set()
        branches = [] if collectBranches else None
        for step in range(1, maxSteps + 1):
            u = self.toOnb(x)
            key = self.orbitKey(u)
            if key in seen:
                return step, branches
            seen.add(key)
            hw = popcount(u)
            b = self.branch(mode, r, hw, key)
            if branches is not None:
                branches.append(b)
            j = 3 + b
            sx = self.sigma(j, x)
            sy = self.sigma(j, y)
            d = x ^ sx
            lam = self.mult(y ^ sy, self.inv(d))
            x3 = self.sqr(lam) ^ lam ^ d
            y3 = self.mult(lam, x ^ x3) ^ x3 ^ y
            x, y = x3, y3
        return -maxSteps, branches

    def step(self, x, y, r, mode):
        """One walk step; returns (x, y, branch)."""
        u = self.toOnb(x)
        key = self.orbitKey(u)
        hw = popcount(u)
        b = self.branch(mode, r, hw, key)
        j = 3 + b
        sx = self.sigma(j, x)
        sy = self.sigma(j, y)
        d = x ^ sx
        lam = self.mult(y ^ sy, self.inv(d))
        x3 = self.sqr(lam) ^ lam ^ d
        y3 = self.mult(lam, x ^ x3) ^ x3 ^ y
        return x3, y3, b

    def orbitOf(self, x):
        return self.orbitKey(self.toOnb(x))

    def fleetWalk(self, starts, extraStarts, r, mode, maxStepsTotal):
        """Campaign metric: W walks in lockstep, shared orbit table.

        A repeat from another walk is the collision the campaign pays for;
        a repeat from a walk's own past means it has entered its rho cycle --
        the campaign's overdue-restart replacement -- so the walk restarts
        from a fresh seed and keeps costing work.  Returns total steps
        walked by the whole fleet until the cross-walk collision."""
        w = len(starts)
        pts = list(starts)
        table = {}
        extra = list(extraStarts)
        steps = 0
        restarts = 0
        while steps < maxStepsTotal:
            for i in range(w):
                x, y = pts[i]
                key = self.orbitOf(x)
                steps += 1
                prev = table.get(key)
                if prev is None:
                    table[key] = i
                elif prev != i:
                    return steps, restarts
                else:
                    # self-cycle: restart the walk from a fresh seed
                    if extra:
                        pts[i] = extra.pop()
                    else:
                        return -steps, restarts + 1
                    restarts += 1
                    continue
                nx, ny, _ = self.step(x, y, r, mode)
                pts[i] = (nx, ny)
                if steps >= maxStepsTotal:
                    return -steps, restarts
        return -steps, restarts


FIELD = None


def fieldForWorker():
    global FIELD
    if FIELD is None:
        FIELD = FastField()
    return FIELD


def crossCheck(f, trials=400):
    """Bit-for-bit agreement with the repository models before measuring."""
    rng = random.Random(20261013)
    onb = repoField.Onb(23)
    curve = repoCurves.Curve(onb)
    for _ in range(trials):
        a = rng.getrandbits(23)
        b = rng.getrandbits(23)
        ra = onb.fromCoords(a)
        rb = onb.fromCoords(b)
        want = onb.toCoords(onb.mul(ra, rb))
        got = f.toOnb(f.mult(f.sigma(0, a) if False else applyTables(f.o2pTabs, a) and 0, b)) if False else None
        got = f.toOnb(f.mult(applyTables(f.o2pTabs, a), applyTables(f.o2pTabs, b)))
        assert want == got, ("mult", a, b, want, got)
        want = onb.toCoords(onb.inv(ra))
        got = f.toOnb(f.inv(applyTables(f.o2pTabs, a)))
        if want != got:
            raise AssertionError("inv mismatch %d: %d vs %d" % (a, want, got))
        if a:
            want = onb.toCoords(onb.frob(ra, 1))
            got = applyTables(f.piTabs, a)
            if want != got:
                raise AssertionError("sigma1 mismatch")
    for j in (3, 7, 10, 18, 26, 34):
        for _ in range(64):
            a = rng.getrandbits(23)
            want = onb.toCoords(onb.frob(onb.fromCoords(a), j))
            got = f.toOnb(f.sigma(j, applyTables(f.o2pTabs, a)))
            assert want == got, ("sigma", j)
    # point arithmetic against the repository curve
    for _ in range(trials):
        p = curve.randomPointOfOrder(f.ell, 4, rng)
        q = curve.randomPointOfOrder(f.ell, 4, rng)
        fp = (applyTables(f.o2pTabs, onb.toCoords(p[0])), applyTables(f.o2pTabs, onb.toCoords(p[1])))
        fq = (applyTables(f.o2pTabs, onb.toCoords(q[0])), applyTables(f.o2pTabs, onb.toCoords(q[1])))
        if fp[0] == fq[0]:
            continue
        want = curve.add(p, q)
        got = f.pointAdd(fp, fq)
        if want is None:
            continue
        assert onb.toCoords(want[0]) == f.toOnb(got[0]), "pointAdd x"
        assert onb.toCoords(want[1]) == f.toOnb(got[1]), "pointAdd y"
    # a 200-step r=8 walk, bit-identical to the repository model
    p0 = curve.randomPointOfOrder(f.ell, 4, random.Random(99))
    x = applyTables(f.o2pTabs, onb.toCoords(p0[0]))
    y = applyTables(f.o2pTabs, onb.toCoords(p0[1]))
    rx, ry = p0
    for _ in range(200):
        u = f.toOnb(x)
        hw = popcount(u)
        j = 3 + ((hw >> 1) % 8)
        sx, sy = f.sigma(j, x), f.sigma(j, y)
        rs = (onb.frob(rx, j % 23) if False else None)
        rs = onb.frob(rx, j)
        rsy = onb.frob(ry, j)
        sxr = onb.toCoords(rs)
        syr = onb.toCoords(rsy)
        assert sxr == f.toOnb(sx), "walk sigma x"
        assert syr == f.toOnb(sy), "walk sigma y"
        nxt = f.pointAdd((x, y), (sx, sy))
        refNext = curve.add((rx, ry), (rs, rsy))
        rx, ry = refNext
        x, y = nxt
        assert onb.toCoords(rx) == f.toOnb(x), "walk x"
        assert onb.toCoords(ry) == f.toOnb(y), "walk y"
    return True


def makeStarts(f, count, seed):
    """Random order-ell start points: repo point once, then fast scalar multiples."""
    onb = repoField.Onb(23)
    curve = repoCurves.Curve(onb)
    p0 = curve.randomPointOfOrder(f.ell, 4, random.Random(seed))
    base = (applyTables(f.o2pTabs, onb.toCoords(p0[0])), applyTables(f.o2pTabs, onb.toCoords(p0[1])))
    rng = random.Random(seed ^ 0x5EED)
    starts = []
    for _ in range(count):
        k = rng.randrange(1, f.ell)
        p = f.pointMul(base, k)
        starts.append(p)
    return starts


def runTrial(args):
    config, seed, base, maxSteps = args
    f = fieldForWorker()
    rng = random.Random(seed)
    starts = []
    for _ in range(FLEET_WORKERS + 8):
        k = rng.randrange(1, f.ell)
        starts.append(f.pointMul(base, k))
    steps, restarts = f.fleetWalk(starts[:FLEET_WORKERS], starts[FLEET_WORKERS:],
                                  config["r"], config["mode"], maxSteps)
    return steps, restarts


def branchAutocorr(f, start, r, mode, n=4096):
    _, branches = f.walk(start, r, mode, 10 ** 9, collectBranches=True)
    b = branches[:n]
    if len(b) < 2:
        return 0.0
    mean = sum(b) / len(b)
    num = sum((b[i] - mean) * (b[i + 1] - mean) for i in range(len(b) - 1))
    den = sum((v - mean) ** 2 for v in b)
    return num / den if den else 0.0


def bootstrapRatio(a, b, resamples=10000, seed=7):
    rng = random.Random(seed)
    n1, n2 = len(a), len(b)
    ma = sum(a) / n1
    mb = sum(b) / n2
    if mb == 0:
        return ma / mb, ma / mb, ma / mb
    vals = []
    for _ in range(resamples):
        sa = sum(a[rng.randrange(n1)] for _ in range(n1))
        sb = sum(b[rng.randrange(n2)] for _ in range(n2))
        if sb:
            vals.append((sa / n1) / (sb / n2))
    vals.sort()
    return vals[int(0.025 * len(vals))], ma / mb, vals[int(0.975 * len(vals))]


def cellProbabilities(r, mode):
    """Exact cell probabilities of the branch under HW ~ Binomial(23, 1/2)."""
    probs = [0.0] * r
    for hw in range(24):
        p = math.comb(23, hw) / (2.0 ** 23)
        b = (hw >> 1) % r if mode == "shift" else hw % r
        probs[b] += p
    return probs


def cyclesCheck(exponents, m, maxLength):
    """Parametrized copy of codegen/cycles.py searchCurve for a widened set."""
    order = repoCurves.curveOrder(m)
    ell = order // 4
    lam = repoCycles.frobeniusScalar(m, ell)
    step = {j: (pow(lam, j, ell) + 1) % ell for j in exponents}
    targets = repoCycles.orbitTargets(lam, m, ell)
    hits = []
    tried = 0
    for k in range(1, maxLength + 1):
        for combo in repoCycles.multisets(tuple(exponents), k):
            tried += 1
            p = 1
            for j in combo:
                p = p * step[j] % ell
            if p in targets:
                hits.append((k, combo, targets[p]))
    return {"ell": ell, "lam": lam, "hits": hits, "tried": tried,
            "expectedChanceHits": tried * (2 * m) / float(ell),
            "degenerate": repoCycles.degeneracies(lam, m, ell)}


def multiplierOrders(exponents, m):
    order = repoCurves.curveOrder(m)
    ell = order // 4
    lam = repoCycles.frobeniusScalar(m, ell)
    out = {}
    for j in exponents:
        mu = (pow(lam, j, ell) + 1) % ell
        out[j] = repoField.multiplicativeOrder(mu, ell) if mu != 1 else 1
    return out, ell


# r = 32 is not well formed at m = 23: j = 3 + b reaches j = 23 there, and
# sigma^23 = id makes that branch a pure doubling.  The m = 131 campaign has
# sigma of order 131, so r = 32 stays distinct there; the m = 23 panel bounds
# the r = 16 question.
FLEET_WORKERS = 8
CONFIGS = [
    {"name": "r8-shift", "r": 8, "mode": "shift"},
    {"name": "r16-shift", "r": 16, "mode": "shift"},
    {"name": "r16-plain", "r": 16, "mode": "plain"},
    {"name": "r8-ideal", "r": 8, "mode": "ideal"},
    {"name": "r16-ideal", "r": 16, "mode": "ideal"},
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--trials", type=int, default=2000)
    ap.add_argument("--max-steps", type=int, default=6000)
    ap.add_argument("--quick", action="store_true", help="200 trials, no multiprocessing")
    ap.add_argument("--seed", type=int, default=20261013)
    ap.add_argument("--workers", type=int, default=8)
    args = ap.parse_args()
    trials = 200 if args.quick else args.trials

    f = FastField()
    t0 = time.time()
    assert crossCheck(f), "cross-check against the repository models failed"
    order = repoCurves.curveOrder(23)
    assert order % 4 == 0 and order // 4 == f.ell, (order, f.ell)
    m = 23
    mOrbits = f.ell // 46
    idealMean = math.sqrt(math.pi * mOrbits / 2.0)
    print("cross-check passed in %.1fs; ell=%d, M=%d x-orbits, ideal mean %.1f steps"
          % (time.time() - t0, f.ell, mOrbits, idealMean), flush=True)

    results = {}
    for ci, config in enumerate(CONFIGS):
        base = makeStarts(f, 1, args.seed + 17 * ci)[0]
        jobs = [(config, args.seed + 101 * ci + t, base, args.max_steps) for t in range(trials)]
        t1 = time.time()
        if args.quick:
            out = [runTrial(j) for j in jobs]
        else:
            from multiprocessing import get_context
            ctx = get_context("spawn")
            with ctx.Pool(args.workers) as pool:
                out = pool.map(runTrial, jobs)
        stepsList = [s for s, _ in out]
        restarts = sum(rr for _, rr in out)
        censored = sum(1 for s in stepsList if s < 0)
        stepsList = [abs(s) for s in stepsList]
        mean = sum(stepsList) / len(stepsList)
        stepsList.sort()
        median = stepsList[len(stepsList) // 2]
        results[config["name"]] = {
            "config": config, "trials": len(stepsList), "censored": censored,
            "restarts": restarts,
            "mean": mean, "median": median,
            "lo25": stepsList[len(stepsList) // 4], "hi75": stepsList[3 * len(stepsList) // 4],
            "raw": stepsList,
        }
        print("%-10s mean %8.1f median %8.1f (ideal %.1f) restarts %d censored %d  [%.0fs]"
              % (config["name"], mean, median, idealMean, restarts, censored, time.time() - t1), flush=True)

    # ratios against the shipping baseline with bootstrap CIs
    base = results["r8-shift"]["raw"]
    ratios = {}
    for name in ("r16-shift", "r16-plain", "r8-ideal", "r16-ideal"):
        lo, point, hi = bootstrapRatio(results[name]["raw"], base)
        ratios[name] = {"lo": lo, "ratio": point, "hi": hi}
        print("ratio %s / r8-shift = %.4f  [95%% CI %.4f .. %.4f]" % (name, point, lo, hi), flush=True)

    # branch autocorrelation diagnostic on one long run per config
    diagStart = makeStarts(f, len(CONFIGS), args.seed + 999)[0]
    autocorr = {}
    for config in CONFIGS:
        ac = branchAutocorr(f, diagStart, config["r"], config["mode"])
        autocorr[config["name"]] = ac
        print("lag-1 branch autocorrelation %-10s %.4f" % (config["name"], ac), flush=True)

    # partition balance, exact
    balance = {}
    for config in CONFIGS:
        probs = cellProbabilities(config["r"], config["mode"])
        balance[config["name"]] = {
            "minCell": min(probs), "maxCell": max(probs),
            "uniform": 1.0 / config["r"],
            "chi2": sum((p - 1.0 / config["r"]) ** 2 / (1.0 / config["r"]) for p in probs) * 1.0,
        }

    # short-cycle recheck for the widened exponent sets
    cycleReports = {}
    for label, exponents, curveM, maxLen in (
            ("m23-ship", range(3, 11), 23, 6),
            ("m23-r16", range(3, 19), 23, 6),
            ("m23-r32", range(3, 35), 23, 6),
            ("m131-ship", range(3, 11), 131, 5),
            ("m131-r16", range(3, 19), 131, 5),
            ("m131-r32", range(3, 35), 131, 5)):
        t2 = time.time()
        rep = cyclesCheck(exponents, curveM, maxLen)
        rep["seconds"] = time.time() - t2
        cycleReports[label] = rep
        print("cycles %-10s tried %d hits %d (expected by chance %.3f) degenerate %d"
              % (label, rep["tried"], len(rep["hits"]), rep["expectedChanceHits"],
                 len(rep["degenerate"])), flush=True)

    orders23, ell23 = multiplierOrders(range(3, 35), 23)
    # m = 131 multiplier orders need the factorization of ell - 1; the
    # short-cycle recheck above already covers the degeneracies that matter.
    orders131, ell131 = {}, cycleReports["m131-r32"]["ell"]

    receipt = {
        "generatedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "trials": trials, "maxSteps": args.max_steps, "seed": args.seed,
        "ell": f.ell, "orbitsM": mOrbits, "idealMean": idealMean,
        "results": {k: {kk: vv for kk, vv in v.items() if kk != "raw"} for k, v in results.items()},
        "ratiosVsShip": ratios,
        "branchAutocorr": autocorr,
        "balance": balance,
        "cycles": cycleReports,
        "multiplierOrders23": orders23, "ell23": ell23,
        "multiplierOrders131": orders131, "ell131": ell131,
    }
    out = Path(__file__).resolve().parent / "receipt.json"
    out.write_text(json.dumps(receipt, indent=1, default=str) + "\n")
    writeReceiptMd(receipt, results, ratios, autocorr, balance, cycleReports,
                  orders23, orders131, ell23, ell131, idealMean, mOrbits, trials)
    print("wrote %s and receipt.json" % ("RECEIPT.md"))


def writeReceiptMd(receipt, results, ratios, autocorr, balance, cycleReports,
                   orders23, orders131, ell23, ell131, idealMean, mOrbits, trials):
    lines = []
    a = lines.append
    a("# Wide-partition walk-quality receipt")
    a("")
    a("Single-walk work-to-first-orbit-repeat on the GF(2^23) test curve,")
    a("built from generated/eccF23.h (permuted type-II ONB, x^23 + x^5 + 1),")
    a("cross-checked bit-for-bit against codegen/field.py and codegen/curves.py")
    a("(multiplication, inversion, sigma^j, point addition, a 200-step walk).")
    a("")
    a("ell = %d, x-orbits M = ell/46 = %d, ideal mean sqrt(pi*M/2) = %.1f steps," % (ell23, mOrbits, idealMean))
    a("%d trials per configuration, max steps %d." % (trials, receipt["maxSteps"]))
    a("")
    a("| config | mean | median | IQR | censored | ratio vs r8-shift | 95% CI |")
    a("| --- | --- | --- | --- | --- | --- | --- |")
    for name, v in results.items():
        r = ratios.get(name)
        a("| %s | %.1f | %.1f | %.1f-%.1f | %d | %s | %s |" % (
            name, v["mean"], v["median"], v["lo25"], v["hi75"], v["censored"],
            ("%.4f" % r["ratio"]) if r else "1.0000",
            ("%.4f-%.4f" % (r["lo"], r["hi"])) if r else "-"))
    a("")
    a("Lag-1 branch autocorrelation over a 4096-step run:")
    a("")
    for name, ac in autocorr.items():
        a("- %s: %.4f" % (name, ac))
    a("")
    a("Partition balance (exact Binomial(23,1/2) cell probabilities):")
    a("")
    a("| config | min cell | max cell | uniform |")
    a("| --- | --- | --- | --- |")
    for name, b in balance.items():
        a("| %s | %.5f | %.5f | %.5f |" % (name, b["minCell"], b["maxCell"], b["uniform"]))
    a("")
    a("Short-cycle recheck (codegen/cycles.py method, widened exponent sets):")
    a("")
    a("| set | curve | multisets tried | hits | expected by chance | degenerate |")
    a("| --- | --- | --- | --- | --- | --- |")
    for label, rep in cycleReports.items():
        a("| %s | %s | %d | %d | %.3f | %d |" % (
            label, rep["ell"], rep["tried"], len(rep["hits"]),
            rep["expectedChanceHits"], len(rep["degenerate"])))
    a("")
    a("Multiplier orders ord_ell(1 + lambda^j), m=23 (ell = %d):" % ell23)
    a("")
    a("j: " + " ".join("%d:%d" % (j, o) for j, o in orders23.items()))
    a("")
    a("Multiplier orders ord_ell(1 + lambda^j), m=131 (ell = %d):" % ell131)
    a("")
    a("j: " + " ".join("%d:%d" % (j, o) for j, o in orders131.items()))
    a("")
    path = Path(__file__).resolve().parent / "RECEIPT.md"
    path.write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
