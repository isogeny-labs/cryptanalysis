# A point-dependent ray-label resolvent and its cost gate

## Exact relation

Fix an ordinary elliptic curve `E/F_p` with a cyclic prime-order subgroup `<G>` of order `r`, and suppose `r = 1 mod 4`. Let `chi_r` be the quadratic character of `F_r^*`. Since `chi_r(-1)=1`, it is well defined on scalar classes modulo sign. Choose one representative `U` from each pair `{u,-u}` in `F_r^*`, and define the x-coordinate resolvent

```text
R(P) = sum_{u in U} chi_r(u) x([u]P)   in F_p.
```

For `Q=[d]G` with `d != 0 mod r`, multiplication by `d` permutes the sign classes. Reindexing the sum gives the exact point relation

```text
R(Q) = chi_r(d) R(G).
```

If `R(G) != 0`, the ratio `R(Q)/R(G)` gives one nontrivial quotient character of the unknown scalar. This is a concrete coordinate-dependent relation; it uses `x(Q)` through the multiples of `Q`. It is also a **generic cyclic-group construction** once an x-coordinate is supplied. CM and horizontal isogenies are not needed for the identity, so their contribution must be demonstrated as a cheaper way to evaluate or represent this resolvent. [pcc:unverified]

## Reproducible CM instance

Use the checked Sage launcher:

```sh
/Volumes/SSD990/cryptanalysis/sage -python - <<'PY'
from sage.all import GF, EllipticCurve, kronecker
p, r = 47, 61
F = GF(p)
E = EllipticCurve(F, [1, 38])
G = E(2, 1)
U = range(1, (r+1)//2)
def chi(k):
    return int(kronecker(k, r))
def resolvent(P):
    return sum((F(chi(u))*(u*P)[0] for u in U), F(0))
assert E.cardinality() == r and (r*G).is_zero()
assert resolvent(G) != 0
assert all(resolvent(d*G) == F(chi(d))*resolvent(G)
           for d in range(1, r))
print({'R_G':int(resolvent(G)), 'R_2G':int(resolvent(2*G)),
       'chi_2':chi(2), 'all_60_checked':True})
PY
```

Observed output: `{'R_G': 17, 'R_2G': 30, 'chi_2': -1, 'all_60_checked': True}`; `30 = -17 mod 47`. The curve has fundamental CM discriminant `-19`, as checked in [the reduction audit](RAY_CLASS_REDUCTION_AUDIT.md). The check confirms the identity for all 60 nonzero scalars on this one curve, including the unknown-scalar form `R(Q)=chi_r(d)R(G)`. It does not extract the full scalar. [pcc:unverified]

## Direct cost versus the full-log reference

The definition has `(r-1)/2` terms. Consecutively generating `G,2G,...,((r-1)/2)G` costs that many group additions to leading order, and doing the same for `Q` costs another such pass for a cold single-target computation. A cached `R(G)` does not remove the target-dependent `Q` pass. At P-192's subgroup order, one pass has `3138550867693340381917894711588029506883597386591421142040` terms, about `2^191`, whereas the negation-aware rho reference `sqrt(pi*r/4)` is about `2^95.826` additions. The direct target pass alone exceeds that full-log reference by about `2^95.174` in counted group additions, while yielding only one character bit. These are derived operation counts, not timings. [pcc:unverified]

To turn this into a useful CM bridge, a proposed smooth-ideal or horizontal-isogeny identity must evaluate the **same** target-dependent resolvent, or a comparably informative ray quotient, at a dramatically lower fully charged cost. A relation that merely permutes `U` or rescales a precomputed `R(G)` by a known ideal scalar does not reveal `chi_r(d)` without evaluating at `Q`. [pcc:unverified]

## Low-degree direct-map gate

There is an elementary restriction on a direct x-only rational map `f(X)=A(X)/B(X)` that exactly equals `chi_r(d)` at every `X=x([d]G)`. Assume `A,B` are coprime, `B` has no zero on those x-values, and set `delta=max(deg A,deg B)`. There are `(r-1)/2` distinct x-values, and each is a root of `A(X)^2-B(X)^2`. The latter polynomial is nonzero because the target character takes both signs, and its degree is at most `2 delta`. Therefore

```text
delta >= ceil((r-1)/4).
```

For P-192 this is `1569275433846670190958947355794014753441798693295710571020`, a 190-bit degree floor. If `r = 3 mod 4`, the quadratic character changes under `d -> -d` while x does not, so **no x-only function of any degree** returns that character on every point. The degree argument applies to a single rational function with exact outputs. It does not lower-bound the time of a compact circuit for a high-degree map, nor does it cover a low-degree inner map followed by a field Legendre symbol. The latter is a separate candidate requiring a precise CM-specific identity and matched controls. [pcc:unverified]
