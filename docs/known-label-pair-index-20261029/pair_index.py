"""Coordinate-only pair index and batched localization; no scalar-log oracle.

Caller supplies verified finite points in an odd-prime-order subgroup, one
orientation per distinct abscissa. The index does not certify those assumptions.
Python-FLINT product/remainder trees implement the polynomial operations.
"""
from itertools import combinations
from functools import lru_cache

from flint import fmpz_mod_poly_ctx


@lru_cache(maxsize=32)
def polynomial_context(prime):
    return fmpz_mod_poly_ctx(prime)


def product_tree(polys):
    if not polys:
        raise ValueError('nonempty product required')
    tree = [list(polys)]
    while len(tree[-1]) > 1:
        layer = tree[-1]
        tree.append([layer[i] * layer[i+1] if i+1 < len(layer) else layer[i]
                     for i in range(0, len(layer), 2)])
    return tree


def evaluate_many(poly, values, prime):
    """Monic remainder tree; repeated evaluation coordinates are allowed."""
    if not values:
        return []
    tree = product_tree([polynomial_context(prime)([-int(x) % prime, 1]) for x in values])
    residues = [poly % tree[-1][0]]
    for layer in reversed(tree[:-1]):
        residues = [residues[i//2] % divisor for i, divisor in enumerate(layer)]
    return [int(rem[0]) for rem in residues]


def pair_factor(prime, curve_a, curve_b, x, y):
    """S_3(x,y,Z), with distinct x,y in F_p; no leaf inversion."""
    x, y = x % prime, y % prime
    if x == y:
        raise ValueError('distinct abscissae required')
    return polynomial_context(prime)([
        (x*y-curve_a)**2-4*curve_b*(x+y),
        -2*((x+y)*(x*y+curve_a)+2*curve_b),
        (x-y)**2])


class PairIndex:
    def __init__(self, prime, curve_a, curve_b, abscissae):
        xs = [int(x) % prime for x in abscissae]
        if prime <= 3 or len(xs) < 2 or len(set(xs)) != len(xs):
            raise ValueError('p>3 and at least two distinct abscissae required')
        self.prime, self.xs = prime, xs
        self.pairs = list(combinations(range(len(xs)), 2))
        self.tree = product_tree([
            pair_factor(prime, curve_a, curve_b, xs[i], xs[j])
            for i, j in self.pairs])

    @property
    def polynomial(self):
        return self.tree[-1][0]

    def coverage_size(self):
        """Distinct target x values, assuming all supplied points are usable.

        This derivative shortcut requires total degree < p. It refuses the
        inseparable/large-degree case rather than reporting a wrong count.
        """
        h = self.polynomial
        if h.degree() >= self.prime:
            raise ValueError('coverage shortcut requires degree < p')
        return int(h.degree() - h.gcd(h.derivative()).degree())

    def match_many(self, abscissae):
        """Return every matching unordered pair for each target coordinate.

        No root extraction or per-target scan of all pair factors is used.
        Total output incidences are charged; they can be quadratic per query.
        """
        xs = [int(x) % self.prime for x in abscissae]
        out = [[] for _ in xs]
        root_values = evaluate_many(self.polynomial, xs, self.prime)

        def visit(level, node, active):
            if not active:
                return
            if level == 0:
                for query in active:
                    out[query].append(self.pairs[node])
                return
            for child in (2*node, 2*node+1):
                if child >= len(self.tree[level-1]):
                    continue
                vals = evaluate_many(self.tree[level-1][child],
                                     [xs[q] for q in active], self.prime)
                visit(level-1, child,
                      [q for q, value in zip(active, vals) if value == 0])

        visit(len(self.tree)-1, 0,
              [q for q, value in enumerate(root_values) if value == 0])
        return out


def signed_witnesses(index, vertices, targets, labels, order, add, neg):
    """Localize and independently check Ri + sign*Rj = target_sign*T.

    Point operations are supplied by the caller. Identity targets are returned
    separately, never silently dropped. Label/scalar replay and construction
    bookkeeping are the caller's additional charged work.
    """
    if len(vertices) != len(index.xs) or len(targets) != len(labels):
        raise ValueError('point/label dimensions differ')
    if any(point is None or point[0] % index.prime != x
           for point, x in zip(vertices, index.xs)):
        raise ValueError('vertices do not match indexed abscissae')
    finite = [q for q, point in enumerate(targets) if point is not None]
    matches = index.match_many([targets[q][0] for q in finite])
    edges, identities, cache, additions = [], [], {}, 0
    for q, target in enumerate(targets):
        if target is None:
            a, b = labels[q]
            identities.append({'query': q, 'label': (a % order, b % order),
                               'candidate_d': (-a*pow(b % order, -1, order)) % order
                               if b % order else None})
    for q, pairs in zip(finite, matches):
        for i, j in pairs:
            if (i, j) not in cache:
                cache[i, j] = ((1, add(vertices[i], vertices[j])),
                               (-1, add(vertices[i], neg(vertices[j]))))
                additions += 2
            found = []
            for sign, result in cache[i, j]:
                for target_sign in (1, -1):
                    if result == (targets[q] if target_sign == 1 else neg(targets[q])):
                        label = tuple(target_sign*c % order for c in labels[q])
                        found.append((i, j, sign, label))
            if len(found) != 1:
                raise ValueError('pair polynomial failed actual point verification')
            edges.extend(found)
    return {'edges': edges, 'identity_targets': identities,
            'witness_group_additions': additions}
