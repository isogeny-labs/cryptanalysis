# Prime-to-order isogenies and point descent

## The rational-point cokernel

Let `E/F_p` have `#E(F_p) = r` prime. Let `phi:E -> E'` be an
`F_p`-rational separable isogeny of degree `n` with `gcd(n,r)=1`.
Its kernel has `n` geometric points, so its intersection with the
order-`r` group `E(F_p)` is trivial. The restriction
`phi:E(F_p) -> E'(F_p)` is therefore injective. Isogenous curves over
`F_p` have equal point counts; both groups have order `r`, making the
restriction bijective. The same conclusion holds for a composite of
prime-to-`r` isogenies. [pcc:unverified]

On the PR's horizontal degree-5 edge over `F_1009`, a Sage enumeration
finds `1069` source points, `1069` distinct images, and `1069`
codomain points. Replay with
`E=EllipticCurve(GF(1009),[4,10])`,
`phi=E.isogenies_prime_degree(5)[0]`, and
`len({phi(P) for P in E.points()})`. This checks one finite instance of
the restriction theorem, not its general proof. [pcc:unverified]

The exact sequence of Galois modules associated with `phi` gives a
connecting homomorphism

```text
delta_phi: E'(F_p) / phi(E(F_p)) -> H^1(F_p, ker(phi)).
```

Its domain is the zero group. Thus the standard isogeny-descent class
of any rational target on `E'` is trivial. This is a statement about
that cokernel map; it does not say that coordinate functions of an
isogeny are constant, or that every point-dependent construction on
an isogenous curve is impossible. [pcc:unverified]

For `Q=[d]G`, the unique rational preimage of `phi(Q)` is `Q` itself
under the restricted inverse map, and
`phi(Q)=[d]phi(G)`. Transporting both marked points preserves their
unknown scalar. An algorithm that uses the isogeny to improve a
coordinate-dependent relation solver must show an evaluation or
relation-cost gain beyond these identities. [pcc:unverified]

## Application to smooth horizontal chains

Suppose a principal ideal relation is represented by
`alpha=a+b*pi` and its horizontal factorization gives an isogeny
chain of total degree `N(alpha)` coprime to `r`. Every factor degree
is then coprime to `r`, so each step is a bijection on rational
points. On `E(F_p)`, Frobenius is the identity and `alpha` acts as the
known scalar `[a+b] mod r`; this scalar is nonzero because its kernel
on the rational group is trivial. The principal relation therefore
does not furnish a nontrivial isogeny-descent class of `Q` or a new
equation for `d`. [pcc:unverified]

The assumption `gcd(N(alpha),r)=1` matters. The endomorphism `1-pi`
has degree `r` and kills `E(F_p)`, while its dual has degree `r` and
acts invertibly on P-192's rational group. Degree divisible by `r`
alone does not determine the rational restriction. The separate
[`1-pi` analysis](FROBENIUS_MINUS_ONE_GATE.md) examines its nontrivial
preimage torsor and the missing scalar orientation. [pcc:unverified]

## Remaining discriminant

A useful successor must construct a relation that depends on `Q`'s
coordinates outside the zero cokernel above, then show that the
horizontal chain changes its evaluation cost or relation yield against
a same-point-set control. The existing [joint S4 screen](README.md)
and [EDS residue screen](EDS_SMOOTH_SCALAR_GATE.md) test two such
directions. This gate proves only the prime-to-`r` rational-point and
standard isogeny-descent statements. [pcc:unverified]
