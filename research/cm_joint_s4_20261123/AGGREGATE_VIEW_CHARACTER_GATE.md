# Bounded products of horizontal-view characters

The [outer-character degree gate](OUTER_CHARACTER_DEGREE_GATE.md)
applies to one rational function followed by a field quadratic
character. Taking a product of signs from several horizontal views
still has that form when the list and maps are fixed in advance.
This note applies its existing bound to that specific aggregate;
it is not a new lower bound on every point-to-ideal construction.
[pcc:unverified]

Let `phi_i:E -> E_i` be rational isogenies of degrees `e_i`, and
let `h_i in F_p(E_i)` be nonzero rational functions of degrees `d_i`
as maps to the projective line. Choose integer exponents `c_i`
independently of the supplied point and set

```text
F(P) = product_i h_i(phi_i(P))^c_i,
bit(P) = chi_p(F(P)).
```

Assume every factor is finite and nonzero at each nonidentity
`P in E(F_p)`. Pullback multiplies function degree by `e_i`;
pole degrees add under products, and inversion exchanges zeros and
poles. Thus `deg(F) <= sum_i |c_i| e_i d_i`. If the factors are
already quadratic signs, even `c_i` can be removed without changing
the bit. The bound does not require independent factors, distinct
endpoints, or a claim about how fast the maps are evaluated.
[pcc:unverified]

For the exact P-192 parameters, the existing gate proves that an
everywhere-exact identity `bit([u]G)=chi_r(u)` requires
`deg(F)>=3961408125713216879677197517` under the stated
regularity assumptions. In the concrete bounded family of at most
100 factors with `|c_i|=1`, `e_i<=100`, and `d_i<=100`, the degree
is at most **1,000,000**, so no such fixed product can be an exact
ray-label evaluator. This is a statement about this bounded
family, not about long compositions or high-degree compact circuits.
[pcc:unverified]

The same gate's full-group correlation inequality gives more than
the failure of exactness. With its `H=2^24`, `D<=1,000,000`, and
the exact P-192 `p,r`, the [integer certificate](aggregate_view_character_bound.py)
shows `|S|/(r-1)<1/3600`, where

```text
S = sum_{u=1}^{r-1} bit([u]G) chi_r(u).
```

Even after choosing the better global output sign, agreement on the
**entire** nonidentity point group is therefore strictly below
`1/2+1/7200` (about `0.500139`). This is a derived uniform bound,
not a sampled success rate or a targetwise prediction. It leaves
target-adaptive factor selection, exceptional-point branches,
sequential circuits whose degree grows under composition, and
other output functions outside its scope. [pcc:unverified]

Smooth ideal relations can provide known horizontal maps and known
residues, but multiplying a bounded number of low-degree local
quadratic signs does not turn those known residues into a useful
fixed full-group ray-character predictor. A surviving proposal must
name the coordinate operation that escapes this product form and
price its construction, target evaluation, and full recovery against
the matched scalar and same-target rho controls. [pcc:unverified]

Reproduce the exact integer inequalities with
`python3 research/cm_joint_s4_20261123/aggregate_view_character_bound.py`.
