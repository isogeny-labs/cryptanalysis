# Degree gate for an exact outer quadratic character

The [direct rational-map gate](RAY_LABEL_CHARACTER_GATE.md) does not cover
`chi_p(f(Q))`: the field quadratic character is an operation after evaluating
the rational function. This note gives a separate degree bound for that exact
form. It applies to a function with coefficients chosen from the curve, the
base point, or horizontal-isogeny data. It does **not** bound the arithmetic
circuit size for evaluating a high-degree function. [pcc:unverified]

## Statement

Let `p` be odd, let `#E(F_p)=r` be an odd prime, and fix a generator `G`.
Let `chi_p` and `chi_r` be the quadratic characters of `F_p` and `F_r`.
Suppose a nonzero `f in F_p(E)` is finite and nonzero at every nonidentity
`F_p`-point and satisfies

```text
chi_p(f([d]G)) = chi_r(d)       for every 1 <= d < r.             (1)
```

If `m` is an integer with `|m| >= 2`, `p` not dividing `m`, and
`chi_r(m)=-1`, and `D=deg(f:E -> P^1)`, then

```text
D >= (p - 1 - 2 sqrt(p)) / (2 (m^2 + 1) sqrt(p)).                 (2)
```

The bound is useful when the right side is positive. For P-192, `m=3`
works, and (2) gives the integer floor

```text
D >= 3961408125713216879677197517 > 2^91.67.                 (3)
```

This is a bound for a **single rational function followed by one field
Legendre symbol**. It also applies to an `x`-only rational function, since
such a function belongs to `F_p(E)`. The regularity hypothesis excludes
special-case handling of zeros and poles at rational points. [pcc:unverified]

## Proof

Put `h=(f o [m])/f`. Multiplication by `m` permutes the nonidentity
`F_p`-points. Multiplicativity of quadratic characters and (1) give

```text
chi_p(h(P)) = chi_r(m) = -1    for every P in E(F_p) \ {O}.       (4)
```

First, `h` is not a square in the geometric function field
`F_pbar(E)`. Otherwise its divisor has even valuation everywhere. Let
`B` be the finite set of geometric points at which `div(f)` has odd
valuation. Since `[m]` is etale of degree `m^2`, the parity condition
on `div(h)` says `B=[m]^{-1}(B)`. The set on the right has `m^2 |B|`
points, so `B` is empty. Thus `div(f)=2A` for a divisor `A` defined over
`F_p`. Its class in `Pic^0(E)(F_p)=E(F_p)` is 2-torsion and hence zero,
because `r` is odd. Consequently `f=c v^2` for `c in F_p^*` and
`v in F_p(E)`. Its field character would be constant on all the points
in (1), contrary to the nonconstant character `chi_r`. This proves the
geometric nonsquare claim. [pcc:unverified]

Let `C` be the smooth projective curve with function field
`F_p(E)(sqrt(h))`. The geometric nonsquare claim makes it geometrically
connected. Let `t` be the number of geometric points of `E` at which
`h` has odd valuation. The degree-two cover `C -> E` branches exactly
there. Riemann--Hurwitz, with `g(E)=1`, gives `g(C)=1+t/2`. By (4), no
nonidentity rational point of `E` has a rational point above it on `C`.
The fiber above `O` contributes at most two, so `#C(F_p)<=2`. The
Hasse--Weil bound therefore yields

```text
p + 1 - (2+t) sqrt(p) <= #C(F_p) <= 2,
and hence t >= (p-1)/sqrt(p) - 2.                               (5)
```

The pole degree of `f o [m]` is `m^2 D`. The pole degree of `h` is at
most `(m^2+1)D`. Its zero and pole divisors each have that degree, so
the number of their distinct odd-valuation points is at most
`2(m^2+1)D`. Combine this with (5) to obtain (2). [pcc:unverified]

The two external ingredients are the [Riemann--Hurwitz formula for
smooth curves](https://stacks.math.columbia.edu/tag/0C1B) and the
[Hasse--Weil bound for a genus-`g` curve](https://math.mit.edu/~poonen/papers/Qpoints.pdf)
(Corollary 7.2.1). The degree bound above is the stated deduction from
these standard results; no novelty claim is made. [pcc:unverified]

## Partial agreement: a 75% gate for small degree

The same argument also constrains a strong but imperfect predictor.
Retain the hypotheses on `E`, `G`, `f`, and `m`, except replace (1) by a
count: let `e` of the `r-1` nonidentity points have
`chi_p(f([d]G)) != chi_r(d)`. If `h=(f o [m])/f` is geometrically a
square, the divisor argument above makes `f=c v^2` over `F_p`, so its
sign is constant and `e=(r-1)/2`. Otherwise,

```text
e >= (p - 1 - (2 + 2(m^2+1)D) sqrt(p)) / 4.                     (6)
```

To see this, call a point erroneous when its predicted sign differs
from `chi_r(d)`. For `chi_p(h(P))=+1`, the predictions at `P` and
`[m]P` agree although the true signs differ. At least one endpoint
is erroneous. The permutation `P -> [m]P` gives each erroneous point
one incoming and one outgoing directed edge, hence at most `2e`
points have `chi_p(h(P))=+1`. The quadratic cover therefore has at
most `2+4e` rational points. Applying the same Hasse--Weil and branch
count inequalities as above yields (6). The right side may be
negative, in which case it gives no restriction. [pcc:unverified]

For P-192 and `m=3`, the nonsquare case becomes

```text
e >= (p - 1 - (2 + 20D) sqrt(p)) / 4.                           (7)
```

For a family with fixed `m`, `r ~ p`, and `D=o(sqrt(p))`, the agreement
fraction is at most `3/4 + o(1)`; the geometrically-square case has
exactly `1/2` agreement. At the fixed P-192 parameters, (7) gives the
corresponding explicit bound for any proposed `D`. In particular, one field Legendre symbol
of a fixed-degree horizontal-map coordinate expression cannot be a
near-perfect ray-label predictor on P-192 under these regularity
hypotheses. This **does not** exclude a weak advantage over `1/2`,
a high-degree compact circuit, combinations of predicates, or a
partial-label recovery method. No sample correlation or runtime
result is inferred from this bound. [pcc:unverified]

## Exact P-192 arithmetic and remaining gate

The following calculation checks `chi_r(3)=-1` and finds the least
integer satisfying the necessary squared inequality in (2). It uses
integer arithmetic throughout:

```sh
python3 - <<'PY'
p = 6277101735386680763835789423207666416083908700390324961279
r = 6277101735386680763835789423176059013767194773182842284081
assert pow(3, (r-1)//2, r) == r-1
assert p % 3 and r % 3
lo, hi = 0, 1 << 100
while lo < hi:
    mid = (lo + hi) // 2
    if (20*mid + 2)**2 * p >= (p-1)**2:
        hi = mid
    else:
        lo = mid + 1
assert not (20*(lo-1) + 2)**2 * p >= (p-1)**2
print(lo)
PY
```

This result closes constant and other small-degree exact predicates of
form (1) at P-192, including the bounded class examined in the
[finite outer-character screen](LOW_DEGREE_OUTER_CHARACTER_SCREEN.md).
It does not exclude a compact high-degree evaluation circuit, a
multistage predicate, a partial or probabilistic label, or an index
calculus relation that uses point coordinates in another way. It also
does not attribute any advantage to horizontal isogenies. The next
positive candidate still needs an exact point-dependent relation,
matched native and transported yield, and a cold full-recovery cost
case against rho. [pcc:unverified]
