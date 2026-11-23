# Proof map for joint pair-family intersection

Let `A=(X,Y)` lie on the binary curve `Y²+XY=X³+1`, and fix a target
point `K`. For `X≠x(K)`, the ordinary group law expresses the translated
coordinate `x(K−A)` as `u(X)+v(X)Y`, with rational functions `u,v`. The
implementation works modulo the first-family polynomial `f_A(X)`, which
has one factor for each distinct first-family `x` coordinate. It handles
the exceptional factor `X+x(K)` by direct point checks.

Given a second-family coordinate condition represented in this quadratic
algebra as `U(X)+V(X)Y`, its norm is

`U² + U V X + V²(X³+1)`.

At an actual first-family `x`, the norm vanishes exactly when the condition
vanishes at one of the two curve `y` branches. A GCD with `f_A` therefore
retains all compatible `x` coordinates. The implementation reconstructs
both points over each retained coordinate, checks the exact group sum,
second-family membership, and disjoint folded columns.

| Result | Lean declaration | Exact hypotheses and status |
| --- | --- | --- |
| Quadratic norm identity | `QuadraticNorm.norm_identity` in [QuadraticNorm.lean](QuadraticNorm.lean) | Arbitrary field of characteristic two and the displayed curve equation. Checked with pinned Lean 4.34.1. |
| Norm zero is equivalent to a zero on one of the two `y` branches | `QuadraticNorm.norm_zero_iff_branch` | Same hypotheses; uses absence of zero divisors. Checked. |
| One sparse linearized-polynomial update adds the coset of a binary basis element to its kernel | `LinearizedAnnihilator.extend_kernel_iff` in [LinearizedAnnihilator.lean](LinearizedAnnihilator.lean) | Arbitrary characteristic-two field and additive map `L`. Checked. The concrete eight-element product basis is checked at full rank by the earlier N41 span-oracle run. |

Run `lean QuadraticNorm.lean` and `lean LinearizedAnnihilator.lean` in this
directory. Their retained `#print axioms` outputs list only `propext`,
`Classical.choice`, and `Quot.sound`. Both modules have no admitted proof
obligations or custom axioms. `lean4checker --fresh` was unavailable on
this host.

The Lean theorems formalize the norm and kernel implications. The exact
binary-curve group-law translation, Frobenius rotation, finite source
polynomials, field encoding, polynomial GCD implementation, exceptional
factor removal, and subgroup point checks remain finite implementation
bridges. The [eight-key census](../n41_implicit_pair_oracle_20261019/keys.json),
the [diverse holdout](diverse_keys.json), and two independently enumerated
exceptional controls provide group-law replay for the N41 instances. A
generic Lean proof tying the Sage curve objects to the symbolic coordinate
algebra remains open.
