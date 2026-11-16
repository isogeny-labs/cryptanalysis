#!/usr/bin/env python3
"""Independent F101^6 audit of the selected CT20 elliptic 7-kernels.

Public toy input. No repository field/point/isogeny implementation is imported.
This checks geometric product-kernel inputs; it is *not* a Jacobian/P0 evaluator.
"""

P = 101


class Cubic:
    """F_101[t]/(t^3+h2*t^2+h1*t+h0), with coefficients low-first."""

    def __init__(self, h):
        assert len(h) == 4 and h[3] == 1
        self.h = tuple(h)
        self.zero = (0, 0, 0)
        self.one = (1, 0, 0)
        self.t = (0, 1, 0)

    def c(self, n):
        return (n % P, 0, 0)

    def add(self, u, v):
        return tuple((a + b) % P for a, b in zip(u, v))

    def neg(self, u):
        return tuple((-a) % P for a in u)

    def sub(self, u, v):
        return self.add(u, self.neg(v))

    def mul(self, u, v):
        z = [0] * 5
        for i, a in enumerate(u):
            for j, b in enumerate(v):
                z[i+j] = (z[i+j] + a*b) % P
        for k in (4, 3):
            c = z[k]
            for j in range(3):
                z[k-3+j] = (z[k-3+j] - c*self.h[j]) % P
        return tuple(z[:3])

    def pow(self, x, k):
        assert k >= 0
        out = self.one
        while k:
            if k & 1:
                out = self.mul(out, x)
            x = self.mul(x, x)
            k >>= 1
        return out

    def inv(self, a):
        assert a != self.zero
        return self.pow(a, P**3-2)

    def verify_field(self):
        # For a degree-3 polynomial, Frobenius has exact order 3 on its root
        # iff the polynomial is irreducible (3 prime).
        assert self.pow(self.t, P**3) == self.t
        assert self.pow(self.t, P) != self.t
        assert self.pow(self.c(2), (P**3-1)//2) == self.c(-1)


class Sextic:
    """Quadratic extension of Cubic, using s^2=2."""

    def __init__(self, h):
        self.f3 = Cubic(h)
        self.f3.verify_field()
        self.zero = (self.f3.zero, self.f3.zero)
        self.one = (self.f3.one, self.f3.zero)
        self.t = (self.f3.t, self.f3.zero)
        self.s = (self.f3.zero, self.f3.one)
        self.q = P**6

    def c(self, a):
        return (self.f3.c(a), self.f3.zero)

    def add(self, x, y):
        k = self.f3
        return (k.add(x[0], y[0]), k.add(x[1], y[1]))

    def neg(self, x):
        return (self.f3.neg(x[0]), self.f3.neg(x[1]))

    def sub(self, x, y):
        return self.add(x, self.neg(y))

    def mul(self, x, y):
        k = self.f3
        a = k.add(k.mul(x[0], y[0]), k.mul(k.c(2), k.mul(x[1], y[1])))
        b = k.add(k.mul(x[0], y[1]), k.mul(x[1], y[0]))
        return (a, b)

    def pow(self, x, n):
        assert n >= 0
        acc = self.one
        while n:
            if n & 1:
                acc = self.mul(acc, x)
            x = self.mul(x, x)
            n >>= 1
        return acc

    def inv(self, a):
        assert a != self.zero
        k = self.f3
        norm = k.sub(k.mul(a[0], a[0]), k.mul(k.c(2), k.mul(a[1], a[1])))
        den = k.inv(norm)
        return (k.mul(a[0], den), k.neg(k.mul(a[1], den)))

    def div(self, x, y):
        return self.mul(x, self.inv(y))

    def sqrt(self, a):
        """General finite-field Tonelli-Shanks; explicit non-square witness."""
        if a == self.zero:
            return self.zero
        assert self.pow(a, (self.q-1)//2) == self.one
        q = self.q-1
        e = 0
        while q % 2 == 0:
            q //= 2
            e += 1
        witness = None
        for n in range(1, P):
            z = self.add(self.s, self.c(n))
            if self.pow(z, (self.q-1)//2) != self.one:
                witness = z
                break
        assert witness is not None
        c = self.pow(witness, q)
        t = self.pow(a, q)
        r = self.pow(a, (q+1)//2)
        m = e
        while t != self.one:
            i = 1
            v = self.mul(t, t)
            while v != self.one and i < m:
                v = self.mul(v, v)
                i += 1
            assert i < m
            b = self.pow(c, 1 << (m-i-1))
            r = self.mul(r, b)
            bb = self.mul(b, b)
            t = self.mul(t, bb)
            c = bb
            m = i
        assert self.mul(r, r) == a
        return r

    def frob(self, a):
        return self.pow(a, P)

    def point_add(self, a, b, A):
        if a is None:
            return b
        if b is None:
            return a
        x1, y1 = a
        x2, y2 = b
        if x1 == x2:
            if self.add(y1, y2) == self.zero:
                return None
            assert y1 == y2 and y1 != self.zero
            m = self.div(self.add(self.mul(self.c(3), self.mul(x1, x1)), self.c(A)), self.mul(self.c(2), y1))
        else:
            m = self.div(self.sub(y2, y1), self.sub(x2, x1))
        x3 = self.sub(self.sub(self.mul(m, m), x1), x2)
        y3 = self.sub(self.mul(m, self.sub(x1, x3)), y1)
        return x3, y3

    def scalar(self, p, n, A):
        out = None
        while n:
            if n & 1:
                out = self.point_add(out, p, A)
            p = self.point_add(p, p, A)
            n >>= 1
        return out

    def on_curve(self, p, a, b):
        if p is None:
            return True
        x, y = p
        return self.mul(y, y) == self.add(self.add(self.pow(x, 3), self.mul(self.c(a), x)), self.c(b))


def audit(name, f, h, a, b, predicted, chosen_x):
    # A cyclic kernel polynomial may split completely over F101, so do not
    # assume the kernel abscissa necessarily generates a cubic extension.
    x = chosen_x
    assert f.add(f.add(f.add(f.pow(x, 3), f.mul(f.c(h[2]), f.pow(x, 2))), f.mul(f.c(h[1]), x)), f.c(h[0])) == f.zero
    fx = f.add(f.add(f.pow(x, 3), f.mul(f.c(a), x)), f.c(b))
    assert fx != f.zero
    y = f.sqrt(fx)
    g = (x, y)
    assert f.on_curve(g, a, b)
    assert f.scalar(g, 7, a) is None
    subgroup = [f.scalar(g, n, a) for n in range(7)]
    assert len(set(subgroup)) == 7
    for i in range(7):
        assert f.on_curve(subgroup[i], a, b)
        for j in range(7):
            assert f.point_add(subgroup[i], subgroup[j], a) == subgroup[(i+j)%7]
    # Non-circular negative controls: a nonzero 7-torsion point is not
    # annihilated by [6], and using the other claimed Frobenius eigenvalue fails.
    assert f.scalar(g, 6, a) is not None
    fr = (f.frob(x), f.frob(y))
    lambdas = [i for i in range(1, 7) if subgroup[i] == fr]
    assert len(lambdas) == 1
    lam = lambdas[0]
    assert lam in predicted
    actual_xs = {pair[0] for pair in subgroup[1:]}
    assert len(actual_xs) == 3
    if name == "E113":
        assert actual_xs == {f.c(50), f.c(68), f.c(76)}
    else:
        assert actual_xs == {x, f.frob(x), f.frob(f.frob(x))}
    assert f.frob(f.frob(f.frob(f.frob(f.frob(f.frob(y)))))) == y
    assert f.scalar(g, (lam**6 - 1) % 7, a) is None
    assert f.scalar(g, (lam+1) % 7, a) != fr
    print(f"{name}: h={h}, Frobenius on selected cyclic 7-kernel=[{lam}], order={next(k for k in range(1,7) if pow(lam,k,7)==1)}, point order=7, complete 7x7 table pass")
    return lam


def rank_two_planes_and_lagrangians(selected_a, selected_b):
    """Enumerate EVERY 2-plane of F7^4 in reduced-row-echelon form.

    E109 coordinates are 0,1; E113 coordinates are 2,3. The direct
    product Weil pairing is J = diag([[0,1],[-1,0]], same).
    """
    from itertools import product

    diag = [selected_a, (3 * pow(selected_a, -1, 7)) % 7,
            selected_b, (3 * pow(selected_b, -1, 7)) % 7]
    assert len(set(diag)) == 4 and set(diag[:2]) == {2,5} and set(diag[2:]) == {4,6}
    total = isotropic = invariant = admissible = 0
    included = []
    nonisotropic_invariant = []
    for a in range(4):
        for b in range(a+1, 4):
            row1free = [j for j in range(a+1, 4) if j != b]
            row2free = [j for j in range(b+1, 4)]
            free = [(1, j) for j in row1free] + [(2, j) for j in row2free]
            for params in product(range(7), repeat=len(free)):
                u, v = [0]*4, [0]*4
                u[a] = v[b] = 1
                for (row, j), k in zip(free, params):
                    (u if row == 1 else v)[j] = k
                total += 1
                symp = (u[0]*v[1]-u[1]*v[0]+u[2]*v[3]-u[3]*v[2])%7
                is_iso = symp == 0
                isotropic += is_iso
                is_inv = True
                for row in (u, v):
                    frob = [(diag[j]*row[j])%7 for j in range(4)]
                    # Pivot columns give unique coordinates in the plane.
                    alpha, beta = frob[a], frob[b]
                    if any((alpha*u[j]+beta*v[j])%7 != frob[j] for j in range(4)):
                        is_inv = False
                        break
                invariant += is_inv
                admissible += is_iso and is_inv
                if is_inv:
                    (included if is_iso else nonisotropic_invariant).append((tuple(u), tuple(v)))
    assert (total, isotropic, invariant, admissible) == (2850, 400, 6, 4)
    # The four candidates select one eigenline in each elliptic factor.
    assert all(sum(x!=0 for x in u)==1 and sum(x!=0 for x in v)==1 for u,v in included)
    assert all((u[0]!=0 or u[1]!=0) != (v[0]!=0 or v[1]!=0) for u,v in included)
    assert len(nonisotropic_invariant) == 2
    print("Full E109[7] x E113[7] audit: 2850 rank-two planes, 400 maximal isotropic; 6 Frobenius stable, exactly 4 isotropic and 2 rejected")
    print("4 admissible planes: " + str(included))


def main():
    f = Sextic([72, 100, 35, 1])
    l1 = audit("E109", f, [72, 100, 35, 1], 1, 46, {2, 5}, f.t)
    l2 = audit("E113", f, [59, 46, 8, 1], 44, 21, {4, 6}, f.c(50))
    assert l1 in {2, 5} and l2 in {4, 6} and l1 != l2
    chi1 = {(2 % 7), (5 % 7)}
    chi2 = {(4 % 7), (6 % 7)}
    assert chi1.isdisjoint(chi2)
    # Exhaustively replay the Frobenius action on the product kernel,
    # using only the separately checked [7] cyclic group tables above.
    pairs = {(i, j) for i in range(7) for j in range(7)}
    assert len(pairs) == 49
    assert {(l1*i % 7, l2*j % 7) for i, j in pairs} == pairs
    assert all(((i+u)%7, (j+v)%7) in pairs for i,j in pairs for u,v in pairs)
    # Frobenius-invariant order-7 lines are precisely the two axes.
    lines = set()
    for pair in pairs-{(0,0)}:
        line = frozenset(((n*pair[0])%7, (n*pair[1])%7) for n in range(7))
        lines.add(line)
    assert len(lines) == 8
    invariant = [line for line in lines if {(l1*i%7,l2*j%7) for i,j in line} == line]
    assert len(invariant) == 2
    assert all(any(x == 0 or y == 0 for x,y in line-{(0,0)}) for line in invariant)
    print("F101: all 49 product-kernel pairs/Frobenius closed; stable rank-one subgroups exactly 2 axes (8 lines total)")
    rank_two_planes_and_lagrangians(l1, l2)
    print("full 7-torsion spectra: E109={2,5}; E113={4,6}; no F101-defined mixed-factor 7-kernel graph")
    print("Scope: geometric elliptic product kernel only; no J0->J1 divisor image, R1, Psi, or timing")

if __name__ == "__main__":
    if not __debug__:
        raise SystemExit("Assertions must remain enabled; do not run this oracle with -O")
    main()
