# From one ray-character bit to a full-log cost case

The [ray-label resolvent](RAY_LABEL_CHARACTER_GATE.md) and
[factor map](RAY_CHARACTER_FACTOR_MAP.md) give exact, coordinate-dependent
ways to obtain `chi_r(d)` from `Q=[d]G`, but their direct evaluation is
expensive. The [outer-character degree gate](OUTER_CHARACTER_DEGREE_GATE.md)
constrains one proposed compact form. This note asks what full scalar
recovery would cost **if** a faster exact ray-character evaluator were
found. It does not supply such an evaluator. [pcc:unverified]

## The shifted-character reduction

Suppose an oracle `L(E,G,P)` returns `chi_r(u)` whenever `P=[u]G`, with
`L(E,G,O)=0`. It may use CM data and point coordinates; it must also
work on every translated input below. Given the target `Q=[d]G`, a
public shift `a` produces

```text
L(E,G,Q+[a]G) = chi_r(d+a).                                      (1)
```

This is exactly the shifted Legendre-symbol oracle with hidden shift
`d` over `F_r`. The single output at `Q` gives one bit; the translated
outputs give a full hidden-shift instance. A query that happens to make
`Q+[a]G=O` already reveals `d=-a mod r`. Equation (1) is a reduction
from the hypothetical **exact** evaluator, not a cost claim or a
statement about a partial predictor. [pcc:unverified]

[Kaluđerović, Kleinjung, and Kostić, *Improved key recovery on the
Legendre PRF*](https://eprint.iacr.org/2020/098) give a classical
hidden-shift recovery algorithm whose abstract states, under its
heuristic assumptions, expected `O(sqrt(r log log r))` operations on
`Theta(log r)`-bit words with about
`(r (log r)^2 log log r)^(1/4)` oracle queries. Their parameter is the
prime modulus of the Legendre PRF; here it would be the subgroup order
`r`, **not** the curve field size `p`. This is a published possible
full-recovery route conditional on `L`. Its quoted costs are from the
paper, not measured for this curve or this oracle. [pcc:unverified]

## What an end-to-end comparison must charge

For that particular route, a cold single-target cost ledger is

```text
T_full = T_CM_setup + M*T_label + T_shifts + T_hidden_shift
       + T_verify + T_failed_or_censored,
M ~= (r (log r)^2 log log r)^(1/4).                              (2)
```

`T_label` includes evaluation at the translated point, `T_shifts`
includes forming those points or any charged table of them, and
`T_hidden_shift` includes the recovery algorithm's ordinary work,
memory, and preprocessing. A candidate must compare this complete
quantity with same-target rho in common measured units. The published
algorithm's ordinary work already has a `sqrt(r)` exponent, so its
asymptotic statement by itself gives no sub-rho full-log result. It is
an **upper bound for one conditional route**, not a lower bound on all
ways to use character information. [pcc:unverified]

At P-192, the oracle-query expression in (2) has magnitude roughly
`2^52` (logarithm conventions and hidden constants prevent treating
this as an exact count). The direct resolvent needs about `r/2` group
additions for each target-dependent evaluation; using it for every
shift is far beyond the `sqrt(r)` rho scale. The direct factor map has
degree `(r-1)/4` and likewise does not give a cheap query. The
[outer-character result](OUTER_CHARACTER_DEGREE_GATE.md) is a degree
bound, **not** a bound on `T_label`: a compact high-degree circuit
remains possible. [pcc:unverified]

For any rational isogeny `phi` of degree coprime to `r`, using the
transported generator `phi(G)` gives

```text
phi(Q+[a]G) = phi(Q)+[a]phi(G),
L(E',phi(G),phi(Q)+[a]phi(G)) = chi_r(d+a).                        (3)
```

Thus transport leaves the shifted-character instance and its query
information unchanged. A horizontal path could still reduce the
**charged cost per label** through a new coordinate evaluator; (3)
does not presume equal evaluation cost. A matched native-curve
control is needed to attribute any reduction to the horizontal
structure. [pcc:unverified]

## Admission test for the next proposal

A proposed evaluator should first return exact labels for an
independently supplied `Q`, for translated points `Q+[a]G`, and for
known-residue controls such as `[3]G` on P-192. It must identify a
compact operation in which smooth ideals or a horizontal path lower
the cost relative to a native or ordinary-curve control. Then charge
its setup and repeated evaluations through a complete recovery
algorithm, checking `[d]G=Q` independently and comparing the same
target with rho. Smooth principal-ideal relations on their own supply
known residues and do not implement `L`. [pcc:unverified]
