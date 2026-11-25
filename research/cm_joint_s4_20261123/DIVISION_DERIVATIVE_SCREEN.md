# Division-polynomial derivative as a ray-label predicate

## Candidate and falsifier

The prior [ray-label gate](RAY_LABEL_CHARACTER_GATE.md) leaves open a high-degree function with a compact evaluation circuit. The `r`-division polynomial `psi_r(x)` is such a candidate to screen: its degree is `(r*r-1)/2`, yet division-polynomial recurrences can evaluate its value at a point without materializing every coefficient. At an `r`-torsion point `P`, `psi_r(x(P))=0`; the derivative is the first nonzero local value to test. This screen asks whether

```text
Legendre_p(psi_r'(x([d]G)) / psi_r'(x(G))) = chi_r(d)
```

for all nonzero `d mod r`. The equation would turn a target coordinate into the quadratic quotient of its ray label. It is a precise equality to test before any claim about evaluation cost. The analogous rational-kernel polynomial `K(x) = product_{u=1}^{(r-1)/2}(x-x([u]G))` is included to distinguish the full division polynomial from its rational-line factor. [pcc:unverified]

## Exact finite control

On `E/F_47: y^2=x^3+x+38`, `r=61`, `G=(2,1)`, the checks give `deg K=30` and `deg psi_61=1860`. Neither derivative vanishes at the 60 nonzero rational points. With the value at `G` as reference, the Legendre sign of each derivative matches `chi_61(d)` for **28 of 60** scalars. Thus the displayed equality fails for both polynomials. The first compact falsifier is `d=4`: `x([4]G)=19`, `chi_61(4)=+1`, but both derivative ratios have Legendre sign `-1`. [pcc:unverified]

The following command reproduces the complete finite check:

```sh
/Volumes/SSD990/cryptanalysis/sage -python - <<'PY'
from sage.all import GF, EllipticCurve, PolynomialRing

p, r = 47, 61
F = GF(p)
E = EllipticCurve(F, [1, 38])
G = E(2, 1)
R = PolynomialRing(F, 'X')
X = R.gen()
assert E.cardinality() == r and (r*G).is_zero()
K = R.prod(X - (u*G)[0] for u in range(1, (r-1)//2 + 1))
psi = E.division_polynomial(r)
assert K.degree() == 30 and psi.degree() == 1860
for name, poly in [('kernel', K), ('division', psi)]:
    ref = poly.derivative()(G[0])
    assert ref != 0
    matches = 0
    for d in range(1, r):
        ratio = poly.derivative()((d*G)[0]) / ref
        assert ratio != 0
        observed = 1 if ratio**((p-1)//2) == 1 else -1
        expected = 1 if pow(d, (r-1)//2, r) == 1 else -1
        matches += observed == expected
    assert matches == 28
    print(name, {'degree': int(poly.degree()), 'matches': matches,
                 'total': r-1})
PY
```

Observed output: `kernel {'degree': 30, 'matches': 28, 'total': 60}` and `division {'degree': 1860, 'matches': 28, 'total': 60}`. The two predicates agreed pointwise on this control, but this is an observation at one curve, not an identity asserted for other curves. [pcc:unverified]

## Decision

The direct derivative formula fails its exact equivariance requirement before a P-192 cost test is relevant. This does not rule out other functions assembled from division-polynomial values, nor establish that any such function is cheap to evaluate at the required point. A successor must state a new algebraic transformation law, check it on all 60 nonzero scalars here and a separate CM control, then price its evaluation and full single-target use. An observed correlation on one finite curve is insufficient. [pcc:unverified]

Producer claim: `PCC-20261124-cc7020` (unverified). [pcc:unverified]
