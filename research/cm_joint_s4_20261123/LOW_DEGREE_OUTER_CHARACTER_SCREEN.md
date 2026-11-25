# A bounded outer-character screen for the ray label

## Exact candidate class

The [direct rational-map degree gate](RAY_LABEL_CHARACTER_GATE.md#low-degree-direct-map-gate)
does not apply when a small polynomial in `x(Q)` is followed by the field
quadratic character. Here the candidate output is
`epsilon * chi_p(h(x([d]G)))`, where `epsilon` may be either sign and `h`
is a monic polynomial of degree one or two over `F_p`. Any zero output
fails an exact label test. The target is `chi_r(d)` on one representative
of each pair `{d,-d}`. Scaling a nonzero polynomial only chooses
`epsilon`, so the monic search exhausts this stated class. It also covers
the field character of a nonvanishing linear-fractional function
`A(x)/B(x)` with `deg A, deg B <= 1`: on the tested points,
`chi_p(A/B)=chi_p(AB)`, and the product has degree at most two.
[pcc:unverified]

This is a retrospective **exact finite enumeration**, with no timing or
statistical significance claim. The first two curves share `p=47` but
have different prime orders and fundamental CM discriminants: the
existing `D=-19`, `r=61`, `G=(2,1)` instance and
`E:y^2=x^3+5x+8`, `D=-163`, `r=53`, `G=(19,37)`. The latter is the first
nonsingular short Weierstrass curve in lexicographic `(a,b)` order with
53 points over `F_47`. For a same-order transport comparison, the
existing `p=1009`, `r=1069` degree-5 horizontal map is tested on its
source and codomain, for degree-one candidates only. [pcc:unverified]

## Reproduce

From the repository root, run the checked Sage launcher:

```sh
/Volumes/SSD990/cryptanalysis/sage -python - <<'PY'
from sage.all import GF, EllipticCurve

def leg(v, p):
    v %= p
    if v == 0:
        return 0
    return 1 if pow(v, (p-1)//2, p) == 1 else -1

def screen(name, E, G, r, degrees):
    p = int(E.base_field().cardinality())
    assert E.cardinality() == r and G.order() == r and r % 4 == 1
    vals = [(int((u*G)[0]),
             1 if pow(u, (r-1)//2, r) == 1 else -1)
            for u in range(1, (r+1)//2)]
    assert len({x for x, _ in vals}) == len(vals)
    for degree in degrees:
        candidates = [('linear', c, 0) for c in range(p)] if degree == 1 else [
            ('quadratic', a, b) for a in range(p) for b in range(p)]
        nozero = exact = 0
        best = (-1, None, None, None)
        for kind, a, b in candidates:
            signs = [leg(x-a if kind == 'linear' else x*x+a*x+b, p)
                     for x, _ in vals]
            if 0 in signs:
                continue
            nozero += 1
            same = sum(s == t for s, (_, t) in zip(signs, vals))
            opposite = sum(s == -t for s, (_, t) in zip(signs, vals))
            score = max(same, opposite)
            exact += (score == len(vals))
            if score > best[0]:
                best = (score, kind, a, b)
        print(name, degree, {'candidates': len(candidates),
              'nozero': nozero, 'exact': exact,
              'best_nonzero_agreement': best[0], 'of': len(vals),
              'best_candidate': best[1:]})

F = GF(47)
E1 = EllipticCurve(F, [1, 38])
E2 = EllipticCurve(F, [5, 8])
screen('D-19', E1, E1(2, 1), 61, (1, 2))
screen('D-163', E2, E2(19, 37), 53, (1, 2))

F = GF(1009)
E3 = EllipticCurve(F, [4, 10])
G3 = E3.gens()[0]
phi = E3.isogenies_prime_degree(5)[0]
screen('source-1009', E3, G3, 1069, (1,))
screen('codomain-1009', phi.codomain(), phi(G3), 1069, (1,))
PY
```

Exact output, with `best_candidate` chosen by the first maximum in the
enumeration order:

| Instance | Degree | Candidates | Nonzero on all x-values | Exact | Best agreement |
| --- | ---: | ---: | ---: | ---: | ---: |
| `D=-19`, `r=61` | 1 | 47 | 17 | 0 | 20/30 |
| `D=-19`, `r=61` | 2 | 2,209 | 1,234 | 0 | 25/30 |
| `D=-163`, `r=53` | 1 | 47 | 21 | 0 | 19/26 |
| `D=-163`, `r=53` | 2 | 2,209 | 1,312 | 0 | 22/26 |
| source, `r=1069` | 1 | 1,009 | 475 | 0 | 307/534 |
| codomain, `r=1069` | 1 | 1,009 | 475 | 0 | 304/534 |

The best coefficients are, in row order, `X-1`, `X^2+4X+10`, `X-2`,
`X^2+13`, `X-403`, and `X-792`; the sign `epsilon` is chosen for the
larger of agreement and opposite agreement. These coefficients were
selected after examining every candidate and are **not** held-out
predictors. The result rejects an exact label identity in this finite
class on these instances. It does not estimate performance at P-192,
exclude a higher-degree or other compact circuit, or prove that the
degree-5 map cannot alter a different evaluator's cost. [pcc:unverified]

The direct P-192 factor-map baseline and rho count remain in the
[factor-map note](RAY_CHARACTER_FACTOR_MAP.md#cold-p-192-cost-and-next-gate).
Since the screened predicates fail to return an exact character even on
these finite instances, there is no full-log cost case to promote from
them. A follow-up candidate must first state an exact or quantified
predictive relation and show that horizontal-isogeny data improve it
under a matched control before charging full recovery. [pcc:unverified]

Sources checked for overlap: shared research KB
`source:6f6cf3ab2d46e51060ae5a79aa51723e` (a proposed division-polynomial
Legendre screen) and `source:c8772f55d67f5ee60c0ad36bded97442`
(a branch-discriminant character filter); local lead atlas match for
`Legendre coordinate quadratic character scalar low degree polynomial`.
Neither establishes this finite exact enumeration. No novelty claim is
made. [pcc:unverified]

Producer claim: `PCC-20261124-254331` (unverified). [pcc:unverified]
