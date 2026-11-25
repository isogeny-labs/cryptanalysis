"""Exact arithmetic-progression certificates and strong index-recovery controls.

For M=2*b*g, put S_i=(i+1/2)P and R_k=T+(2*b*k+b-1/2)P.
The points R_k +/- S_i cover T+jP, 0<=j<M, exactly once. For each allowed
coordinate z, a product tree forms E_z(V)=prod_i S_3(V,x(S_i),z). A remainder
tree evaluates E_z at all x(R_k). This is the explicit O~(s*(b+g)) approach,
not the conjectural O~(B+sqrt(M)) approach. All indices are recovered and
verified, including point-at-infinity and denominator exceptions.
"""
from math import ceil, isqrt
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from flint import nmod_poly


class CountedCurve:
    def __init__(self, E):
        self.E = E; self.ops = 0

    def add(self, P, Q):
        self.ops += 1
        return self.E.add(P, Q)

    def neg(self, P):
        return self.E.neg(P)

    def mul(self, n, P):
        if n < 0:
            return self.mul(-n, self.neg(P))
        total = None
        while n:
            if n & 1:
                total = self.add(total, P)
            n >>= 1
            if n:
                P = self.add(P, P)
        return total


def product_tree(polys):
    tree = [list(polys)]
    while len(tree[-1]) > 1:
        layer = tree[-1]; nxt = []
        for i in range(0, len(layer)-1, 2):
            nxt.append(layer[i]*layer[i+1])
        if len(layer) & 1:
            nxt.append(layer[-1])
        tree.append(nxt)
    return tree


def evaluate_tree(f, tree):
    if not tree or not tree[0]:
        return []
    residues = [f % tree[-1][0]]
    for level in range(len(tree)-2, -1, -1):
        residues = [residues[i//2] % q for i, q in enumerate(tree[level])]
    return [int(r[0]) for r in residues]


def zero_leaves(tree, value, p):
    """Recover every zero factor; no uncharged scan of the original block."""
    found = []
    def visit(level, index):
        if int(tree[level][index](value)):
            return
        if level == 0:
            found.append(index)
            return
        for child in [2*index, 2*index+1]:
            if child < len(tree[level-1]):
                visit(level-1, child)
    if tree and tree[0]:
        visit(len(tree)-1, 0)
    return found


def semaev_factor(E, baby_x, z):
    A, b, p = E.a, E.b, E.p
    return nmod_poly([(baby_x*z-A)**2-4*b*(baby_x+z),
                      -2*((baby_x+z)*(baby_x*z+A)+2*b),
                      (baby_x-z)**2], p)


class SymmetricBlocks:
    def __init__(self, E, P, r, b, g):
        tick = time.process_time()
        self.E, self.P, self.r, self.b, self.g = E, P, r, b, g
        assert b > 0 and g > 0 and 2*b < r and 2*b*g < r
        self.M = 2*b*g; C = self.C = CountedCurve(E)
        half = C.mul((r+1)//2, P)
        babies = [half]
        for _ in range(1, b):
            babies.append(C.add(babies[-1], P))
        assert all(S is not None for S in babies)
        self.babies = babies
        self.baby_index = {S[0]: i for i, S in enumerate(babies)}
        # (b-1/2)P = (b-1)P + P/2.
        self.offset = C.add(C.mul(b-1, P), half)
        self.step = C.mul(2*b, P)
        self.setup_ops = C.ops
        self.setup_cpu_s = time.process_time()-tick
        self.certificates = {}
        self.precompute_cpu_s = 0.0

    def prepare(self, coordinates, points=None):
        tick = time.process_time()
        for z in coordinates:
            if z not in self.certificates:
                self.certificates[z] = product_tree([
                    semaev_factor(self.E, S[0], z) for S in self.babies])
        self.precompute_cpu_s += time.process_time()-tick

    def solve(self, T, coordinates):
        tick = time.process_time(); C = self.C; begin_ops = C.ops
        E, p, b, g = self.E, self.E.p, self.b, self.g
        allowed = set(coordinates); hits = {}; degenerate = 0
        identities = set(); recovered_pairs = set()
        centers = [C.add(T, self.offset)]
        for _ in range(1, g):
            centers.append(C.add(centers[-1], self.step))
        finite = [(k, R) for k, R in enumerate(centers) if R is not None]
        tree = product_tree([nmod_poly([-R[0], 1], p) for k, R in finite]) if finite else []
        compose = recovery = verify = 0.0; max_degree = 0
        def recover(k, i):
            nonlocal verify, degenerate
            if (k, i) in recovered_pairs:
                return
            recovered_pairs.add((k, i))
            rt = time.process_time(); R = centers[k]; S = self.babies[i]
            if R is None or R[0] == S[0]:
                degenerate += 1
            for sign in [-1, 1]:
                point = C.add(R, S if sign == 1 else C.neg(S))
                j = 2*b*k+b+i if sign == 1 else 2*b*k+b-1-i
                assert 0 <= j < self.M
                if point is None:
                    identities.add(j)
                if point is not None and point[0] in allowed:
                    hits[j] = point
            verify += time.process_time()-rt
        for k, R in enumerate(centers):
            if R is None:
                for i in range(b):
                    recover(k, i)
            else:
                i = self.baby_index.get(R[0])
                if i is not None:
                    recover(k, i)
        for z in sorted(allowed):
            rt = time.process_time()
            factors_tree = self.certificates.get(z)
            if factors_tree is None:
                factors_tree = product_tree([semaev_factor(E, S[0], z) for S in self.babies])
                self.certificates[z] = factors_tree
            certificate = factors_tree[-1][0]
            max_degree = max(max_degree, int(certificate.degree()))
            values = evaluate_tree(certificate, tree)
            compose += time.process_time()-rt
            rt = time.process_time()
            candidates = []
            for (k, R), value in zip(finite, values):
                if value == 0:
                    candidates.extend((k, i) for i in zero_leaves(factors_tree, R[0], p))
            recovery += time.process_time()-rt
            for k, i in candidates:
                recover(k, i)
        return {'hits': hits, 'identity_indices': sorted(identities),
                'cpu_s': time.process_time()-tick,
                'group_ops': C.ops-begin_ops, 'certificate_cpu_s': compose,
                'index_recovery_cpu_s': recovery, 'verification_cpu_s': verify,
                'max_certificate_degree': max_degree,
                'coordinate_certificates': len(allowed), 'poles_recovered': degenerate}


def binomial_quadratic_resultant(E, U, B, c, modulus):
    """Res_Z(Z^B-c,S_3(V,U,Z)) modulo a giant-point polynomial in V.

    With S_3=a2*Z^2+a1*Z+a0 and rho_i=a2*root_i, their power sum
    s_B=rho_1^B+rho_2^B follows s_2n=s_n^2-2*(a2*a0)^n.
    The homogeneous norm is a0^B-c*s_B+c^2*a2^B, valid even at a2=0.
    No division by a2, no degree-B root polynomial, and no target lifting.
    """
    assert B >= 2 and B & (B-1) == 0
    p = E.p; V = nmod_poly([0, 1], p)
    a2 = ((V-U)**2) % modulus
    a1 = (-2*((V+U)*(V*U+E.a)+2*E.b)) % modulus
    a0 = ((V*U-E.a)**2-4*E.b*(V+U)) % modulus
    power_sum = -a1; product = (a2*a0) % modulus
    for _ in range(B.bit_length()-1):
        power_sum = (power_sum*power_sum-2*product) % modulus
        product = (product*product) % modulus
    return (a0.pow_mod(B, modulus)-c*power_sum+c*c*a2.pow_mod(B, modulus)) % modulus


class BinomialBlocks(SymmetricBlocks):
    """One binomial certificate for every allowed coordinate simultaneously.

    Current cost: O~(b*g*log B) field work, b+g group additions, plus
    output/index recovery; b*g=M/2. This misses the conjectural target.
    """
    def __init__(self, E, P, r, b, g, B, alpha=1):
        super().__init__(E, P, r, b, g)
        assert (E.p-1) % B == 0 and alpha % E.p
        self.B, self.c = B, pow(alpha, B, E.p)

    def solve(self, T, coordinates=None):
        tick = time.process_time(); C = self.C; begin_ops = C.ops
        E, p, b, g = self.E, self.E.p, self.b, self.g
        hits = {}; identity_indices = set(); degenerate = 0
        centers = [C.add(T, self.offset)]
        for _ in range(1, g):
            centers.append(C.add(centers[-1], self.step))
        finite = [(k, R) for k, R in enumerate(centers) if R is not None]
        eval_tree = product_tree([nmod_poly([-R[0], 1], p) for k, R in finite]) if finite else []
        certificate_cpu = recovery_cpu = verification_cpu = 0.0
        candidates = set()
        # The same baby/giant points expose identity indices, at no extra
        # asymptotic cost. Do not lose this legitimate early DLP opportunity.
        baby_index = self.baby_index
        for k, R in enumerate(centers):
            if R is None:
                candidates.update((k, i) for i in range(b))
            elif R[0] in baby_index:
                candidates.add((k, baby_index[R[0]]))
        max_degree = 0
        if finite:
            rt = time.process_time(); modulus = eval_tree[-1][0]
            leaves = [binomial_quadratic_resultant(E, S[0], self.B, self.c, modulus)
                      for S in self.babies]
            norm_tree = [leaves]
            while len(norm_tree[-1]) > 1:
                layer = norm_tree[-1]; nxt = []
                for i in range(0, len(layer)-1, 2):
                    nxt.append((layer[i]*layer[i+1]) % modulus)
                if len(layer) & 1:
                    nxt.append(layer[-1])
                norm_tree.append(nxt)
            certificate = norm_tree[-1][0]
            max_degree = max((int(z.degree()) for layer in norm_tree for z in layer), default=0)
            values = evaluate_tree(certificate, eval_tree)
            certificate_cpu += time.process_time()-rt
            rt = time.process_time()
            for (k, R), value in zip(finite, values):
                if value == 0:
                    candidates.update((k, i) for i in zero_leaves(norm_tree, R[0], p))
            recovery_cpu += time.process_time()-rt
        rt = time.process_time()
        for k, i in sorted(candidates):
            R, S = centers[k], self.babies[i]
            degenerate += R is None or R[0] == S[0]
            for sign in [-1, 1]:
                point = C.add(R, S if sign == 1 else C.neg(S))
                j = 2*b*k+b+i if sign == 1 else 2*b*k+b-1-i
                if point is None:
                    identity_indices.add(j)
                elif pow(point[0], self.B, p) == self.c:
                    hits[j] = point
        verification_cpu += time.process_time()-rt
        return {'hits': hits, 'identity_indices': sorted(identity_indices),
                'cpu_s': time.process_time()-tick, 'group_ops': C.ops-begin_ops,
                'certificate_cpu_s': certificate_cpu,
                'index_recovery_cpu_s': recovery_cpu,
                'verification_cpu_s': verification_cpu,
                'max_certificate_degree': max_degree,
                'baby_fibers': b, 'giant_modulus_degree': len(finite),
                'poles_recovered': degenerate}


class SequentialBlocks:
    def __init__(self, E, P, M):
        self.E, self.P, self.M = E, P, M
        self.C = CountedCurve(E); self.setup_ops = 0; self.setup_cpu_s = 0.0

    def solve(self, T, coordinates):
        tick = time.process_time(); C = self.C; ops = C.ops
        allowed = set(coordinates); hits = {}; R = T; identities = []
        for j in range(self.M):
            if R is not None and R[0] in allowed:
                hits[j] = R
            if R is None:
                identities.append(j)
            if j+1 < self.M:
                R = C.add(R, self.P)
        return {'hits': hits, 'identity_indices': identities,
                'cpu_s': time.process_time()-tick, 'group_ops': C.ops-ops}


class IntervalBSGS:
    """Strong generic set-intersection control, with all signed targets.

    A baby table is reused across blocks. Full coordinate extraction and
    index recovery are included. All hits, not merely the first, are returned.
    """
    def __init__(self, E, P, M, s, baby_size=None):
        tick = time.process_time()
        self.E, self.P, self.M = E, P, M
        C = self.C = CountedCurve(E)
        self.b = min(M, max(1, isqrt((2*s+1)*M) if baby_size is None else baby_size))
        self.table = {None: 0}; R = None
        for i in range(1, self.b):
            R = C.add(R, P); self.table[R] = i
        self.step = C.neg(C.add(R, P))
        self.setup_ops = C.ops; self.setup_cpu_s = time.process_time()-tick
        self.targets = {}; self.precompute_cpu_s = 0.0

    def prepare(self, coordinates, points=None):
        tick = time.process_time()
        for x in coordinates:
            if x not in self.targets:
                self.targets[x] = points[x] if points is not None else self.E.lift(x)
        self.precompute_cpu_s += time.process_time()-tick

    def solve(self, T, coordinates):
        tick = time.process_time(); C = self.C; ops = C.ops
        hits = {}; allowed = set(coordinates); targets = [None]; identities = []
        for x in sorted(allowed):
            point = self.targets.get(x)
            if point is None:
                point = self.E.lift(x)
            if point is None:
                continue
            targets.extend([point, self.E.neg(point)])
        for target in targets:
            R = C.add(target, C.neg(T))
            for k in range(ceil(self.M/self.b)):
                i = self.table.get(R)
                if i is not None:
                    j = k*self.b+i
                    if j < self.M:
                        if target is None:
                            identities.append(j)
                        else:
                            hits[j] = target
                if k+1 < ceil(self.M/self.b):
                    R = C.add(R, self.step)
        return {'hits': hits, 'identity_indices': sorted(identities),
                'cpu_s': time.process_time()-tick,
                'group_ops': C.ops-ops}
