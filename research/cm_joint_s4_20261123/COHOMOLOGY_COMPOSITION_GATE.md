# Cohomology of a smooth horizontal chain

## A composite cannot hide a finite-field descent class

Let `E/F_p` have prime rational-group order `r`, and let
`phi:E -> E'` be a separable `F_p`-rational isogeny of degree `n`
coprime to `r`. Write `K=ker(phi)` over an algebraic closure and
`F` for arithmetic Frobenius on `K`. As `#K=n`, a point fixed by `F`
would lie in both `K` and `E(F_p)`, whose orders are coprime. Thus
`K^F=0`. The endomorphism `F-1` of the finite group `K` is injective
and hence bijective. [pcc:unverified]

For a finite étale commutative group over a finite field, a continuous
Galois 1-cocycle is determined by its value at Frobenius, and changing
the lift changes that value by `(F-1)K`. Consequently,

```text
H^1(F_p, K) = K / (F-1)K = 0.
```

This strengthens the zero-cokernel statement in the
[prime-to-order descent gate](PRIME_TO_R_DESCENT_GATE.md): the full
first cohomology group of this isogeny kernel vanishes, not merely
the image of the connecting map on rational points. The argument
also applies to the composite kernel of a separable horizontal chain
whose total degree is coprime to `r`. An intermediate change of curve
or kernel representation cannot create a nonzero class in this
group. [pcc:unverified]

For the PR's degree-5 edge over `F_1009`, the trace is `-59`.
The Frobenius polynomial on 5-torsion reduces to
`X^2 + 59X + 1009 = (X-3)^2 mod 5`. Its stable order-5 kernel
therefore has Frobenius eigenvalue `3`, and `F-1` acts there by the
unit `2 mod 5`. This is an arithmetic control of the vanishing
calculation on the exact finite edge used in the S4 screen.
[pcc:unverified]

## Degree-r contrast

For `phi=1-pi` on a prime-order curve, `K=E(F_p)` has order `r`
and Frobenius fixes every element. Then `(F-1)K=0` and
`H^1(F_p,K)` is isomorphic to `K`. Given `Q` and a geometric
preimage `T` with `(1-pi)T=Q`, its Frobenius cocycle is
`pi(T)-T=-Q=-[d]G`. This is the nonzero cohomological point relation
derived in the [`1-pi` analysis](FROBENIUS_MINUS_ONE_GATE.md).
Its class retains `Q` as a point; converting that class to the
coefficient `d` still requires an orientation relative to `G`.
[pcc:unverified]

This contrast does not exclude coordinate-dependent relations
produced by summation polynomials, division polynomials, a cover, or
an auxiliary variety. It specifies what a smooth prime-to-`r`
isogeny chain cannot contribute through its kernel cohomology.
Any proposed point bridge outside this group still needs a
same-target relation and a charged cost comparison. [pcc:unverified]

The isogeny connecting-map setup is standard; see
[Stoll, *Explicit Isogeny Descent on Elliptic Curves*](https://www.mathe2.uni-bayreuth.de/stoll/papers/isogeny-descent.pdf).
The finite-field vanishing above follows directly from the displayed
Frobenius calculation. [pcc:unverified]
