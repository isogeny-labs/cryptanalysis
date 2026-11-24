# An exact coordinate map for the quadratic ray label

## Construction and proof

Let `E/F_p` have odd characteristic and a cyclic subgroup `<G>` of prime
order `r = 1 mod 4`. Write `chi` for the quadratic character modulo `r`.
The nonzero subgroup points have `(r-1)/2` distinct x-coordinates. Since
`chi(-u)=chi(u)`, these split into disjoint sets

```text
X_+ = {x([u]G) : chi(u)=+1},    X_- = {x([u]G) : chi(u)=-1},
```

each of cardinality `n=(r-1)/4`. Define monic polynomials over `F_p`

```text
F_+(X) = product_{x in X_+}(X-x),
F_-(X) = product_{x in X_-}(X-x),
f_G(X) = (F_-(X)-F_+(X))/(F_-(X)+F_+(X)).
```

For every `Q=[d]G != O`, exactly one factor vanishes at `x(Q)` and the
other does not. The denominator is therefore nonzero there, and
`f_G(x(Q))=chi(d)`. In particular `f_G(x(G))=1`. Replacing the generator by
`[v]G` exchanges the two factors exactly when `chi(v)=-1`; the resulting
map is multiplied by `chi(v)`. This is an explicit, generator-oriented,
coordinate-dependent one-bit relation for an independently supplied point.
It is generic to any such prime-order subgroup and does not use a horizontal
isogeny. [pcc:unverified]

The numerator has degree at most `n-1` because both factors are monic.
The denominator has degree `n` because its leading coefficient is `2`.
There is no common root: a common root would make both `F_+` and `F_-`
vanish. Thus the rational-map degree is exactly `n`, attaining the
[direct x-map lower bound](RAY_LABEL_CHARACTER_GATE.md#low-degree-direct-map-gate).
This is a statement about a single exact rational map, not a runtime lower
bound for every circuit or a map followed by a character operation.
[pcc:unverified]

The product `F_+ F_-` is the rational subgroup's x-kernel polynomial. The
partition realizes the same abstract quadratic scalar character as the
[quadratic ray subfield](QUADRATIC_RAY_SUBFIELD.md), after orienting at `G`.
This does not construct a point-labelled embedding of that number field,
or prove that its two local square roots are represented by these two
particular factors. [pcc:unverified]

## Finite CM control

The following exact computation checks every nonzero scalar on the
`D=-19`, `p=47`, `r=61` curve used in the adjacent ray audits:

```sh
/Volumes/SSD990/cryptanalysis/sage -python - <<'PY'
from sage.all import GF, EllipticCurve, PolynomialRing
p, r = 47, 61
F = GF(p)
E = EllipticCurve(F, [1, 38])
G = E(2, 1)
R = PolynomialRing(F, 'X')
X = R.gen()
plus, minus = set(), set()
assert E.cardinality() == r and (r*G).is_zero()
for d in range(1, r):
    x = (d*G)[0]
    (plus if pow(d, (r-1)//2, r) == 1 else minus).add(x)
assert len(plus) == len(minus) == 15 and not plus.intersection(minus)
Fp = R.prod(X-x for x in plus)
Fm = R.prod(X-x for x in minus)
f = (Fm-Fp)/(Fm+Fp)
assert all(f((d*G)[0]) == (1 if pow(d, 30, 61) == 1 else -1)
           for d in range(1, 61))
print({'plus_degree': Fp.degree(), 'minus_degree': Fm.degree(),
       'map_degree': max((Fm-Fp).degree(), (Fm+Fp).degree()),
       'at_G': int(f(G[0])), 'at_2G': int(f((2*G)[0])),
       'all_60_checked': True})
PY
```

Observed output: `{'plus_degree': 15, 'minus_degree': 15,
'map_degree': 15, 'at_G': 1, 'at_2G': 46, 'all_60_checked': True}`.
Here `46=-1 mod 47`, agreeing with `chi_61(2)=-1`. This checks the
construction on one finite CM instance, rather than its claimed cost at
cryptographic size. [pcc:unverified]

## What horizontal transport preserves

Let `phi:E -> E'` be an `F_p`-rational isogeny whose degree is coprime to
`r`, and put `H=phi(G)`. It is injective on `<G>`, so `H` also has order
`r`. For every nonzero `Q=[d]G`, `phi(Q)=[d]H`, hence

```text
f_H(x(phi(Q))) = chi(d) = f_G(x(Q)).
```

This is an exact commutation law for the marked factor maps. If `phi` is
an endomorphism acting by the known scalar `lambda` on `<G>`, then the
same-source version reads
`f_G(x(phi(Q)))=chi(lambda) f_G(x(Q))`. For the earlier
`D=-19` smooth-norm element `1+pi` of norm `35=5*7`, rational Frobenius
acts as one, so `lambda=2 mod 61` and the factor map changes sign. The
known sign does not supply the unknown `chi(d)` without evaluating the
map at a target point. [pcc:unverified]

The following independent degree-5 horizontal instance checks the
marked-map equality for every nonzero scalar. Its trace discriminant is
the fundamental `-555`, so the degree-5 isogeny stays on the maximal-order
crater, as detailed in the [joint screen](README.md):

```sh
/Volumes/SSD990/cryptanalysis/sage -python - <<'PY'
from sage.all import GF, EllipticCurve, PolynomialRing
p, r = 1009, 1069
F = GF(p)
E = EllipticCurve(F, [4, 10])
G = E.gens()[0]
phi = E.isogenies_prime_degree(5)[0]
H = phi(G)
R = PolynomialRing(F, 'X')
X = R.gen()
def factor_map(P):
    pos, neg = [], []
    for u in range(1, (r+1)//2):
        (pos if pow(u, (r-1)//2, r) == 1 else neg).append((u*P)[0])
    Fp = R.prod(X-x for x in pos)
    Fm = R.prod(X-x for x in neg)
    return (Fm-Fp)/(Fm+Fp), len(set(pos)), len(set(neg))
f, np, nm = factor_map(G)
g, hp, hm = factor_map(H)
assert E.cardinality() == r and H.order() == r
assert np == nm == hp == hm == (r-1)//4
assert all(f((u*G)[0]) == g(phi(u*G)[0]) for u in range(1, r))
print({'p': p, 'r': r, 'degree': phi.degree(),
       'factor_degrees': [np, nm, hp, hm],
       'all_1068_transport_labels_equal': True})
PY
```

Observed output: `{'p': 1009, 'r': 1069, 'degree': 5,
'factor_degrees': [267, 267, 267, 267],
'all_1068_transport_labels_equal': True}`. The proof applies more broadly
than this instance. Transport alone preserves the character and the
`(r-1)/4` factor degree. A codomain-specific compact evaluator could still
improve the *cost*; that would require an explicit construction and a
matched source/generic comparison, rather than the commutation identity.
Producer claim `PCC-20261124-0f2381` is unverified. [pcc:unverified]

## Cold P-192 cost and next gate

At P-192's subgroup order,
`n=1569275433846670190958947355794014753441798693295710571020`,
about `2^190`. Direct setup enumerates `(r-1)/2` subgroup x-values, about
`2^191` group additions to leading order. The two dense coefficient lists
have about `2n` field elements; at 24 bytes per element their raw payload
alone is about `2^195.585` bytes. Horner evaluation of both factors at one
target costs `Theta(n)` field multiplications. These are representation and
operation counts, not measured runtime or a hardware-normalized ratio.
The negation-aware rho reference is about `2^95.826` group additions for
the full scalar. The direct factor-map computation is therefore not a
competitive one-bit route at this size. [pcc:unverified]

The falsifiable next question is whether the **same oriented partition**
has a compact evaluation using CM and smooth-ideal data. A proposal must
give a target-coordinate evaluator, charged construction and per-target
cost, a same-size generic ordinary-curve control, and a route from its
character output to the full scalar with cold total cost below rho. A
compact defining polynomial for `K(sqrt(1-pi))` or another smooth principal
ideal does not by itself compress this map. [pcc:unverified]

Sources checked for overlap: local lead atlas matches for `quadratic ray
character factor polynomial`; shared research KB `source:c8772f55d67f5ee60c0ad36bded97442`
(a branch-discriminant filter), `source:4e186cd15ad83be16e1d054f5a902b66`
(coordinate degree questions), and the adjacent ray-label notes in this
directory. These are adjacent mechanisms; no novelty claim is made.

Producer claim: `PCC-20261124-a61662` (unverified). [pcc:unverified]
