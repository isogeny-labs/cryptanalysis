# Frozen kernel-character versus EDS-normalizer check

## Candidate and prior pilot

For `E/F_p:y²=g(x)` with prime rational group order `r`, define the
monic anti-Frobenius kernel polynomial

```text
K_E(X) = product_{x in F_p, chi_p(g(x))=-1}(X-x).
```

This is the x-kernel polynomial of `1+pi`; its degree is
`(2(p+1)-r-1)/2`. Let `Phi(P)` be the point-computable EDS normalizer
in [Lauter–Stange, Theorem 8](https://arxiv.org/pdf/0803.0728).
The new proposed identity is only at the **field-character** level:
there may be one curve-dependent constant `c_E∈{+1,-1}` such that

```text
chi_p(K_E(x(P))) = c_E * chi_p(y(P)*Phi(P))
```

on every nonidentity rational point. Fix `c_E` by evaluating both
sides at the marked generator. The `D=-19`, `p=47`, `r=61` full
60-point equality with `c_E=+1` was observed before this freeze and
is a pilot, not confirmation. The original y-normalizer ray-label
prediction failed at `d=4`; this is a different, weaker identity.
[pcc:unverified]

## Frozen independent controls

Run the full `d=1,...,52` census on
`E/F_47:y²=x³+5x+8`, `r=53`, `G=(19,37)`, with fundamental CM
discriminant `-163`. On the existing degree-five horizontal pair
over `F_1009`, use `E:y²=x³+4x+10`, `r=1069`, `G=E.gens()[0]`,
the first Sage degree-five edge, and `H=phi(G)` on its codomain
`y²=x³+888x+852`. On each endpoint test the predeclared labels
`1,2,3,5,7,11,13,17`. Do not select a subset after seeing signs.
The script must retain every sign, its curve orientation `c_E`,
all mismatches, kernel degree, and point count. It checks the
normalizer's nonzero division-polynomial ratio and the exact
`Phi(-P)=-Phi(P)` parity identity at every tested point.
[pcc:unverified]

If the full second-curve census and both eight-label horizontal
controls pass, a separate proof and a newly frozen full horizontal
census are next. If either fails, report the first mismatches and
stop this proposed universal equality. Even success would only
provide a compact evaluator for the anti-Frobenius kernel character;
it would not by itself determine the unknown scalar or show a CM
advantage over a generic point computation. [pcc:unverified]
