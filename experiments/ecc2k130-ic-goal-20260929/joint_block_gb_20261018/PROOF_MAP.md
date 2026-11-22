# Joint source-product expansion proof map

The mathematical result used by the joint block solver is an exact
rewrite of a bivariate polynomial whose exponents in each source
product are at most four. Let `F` be a commutative ring with `2=0`.
For Boolean weights `b_i²=b_i`, set `p=Σ b_i a_i`; likewise let
`q=Σ c_j d_j` with `c_j²=c_j`. Then `p²` and `p⁴` are linear in the
`b_i`, while `p³` uses only singleton and pair products of the `b_i`.
The same holds for `q`. Therefore every term `p^r q^s` with
`0≤r,s≤4` expands into monomials with at most two first-source
weights and at most two second-source weights. This includes all 13
terms of the frozen target-conditioned resultant.

| Mathematical step | Lean declaration | Exact hypotheses | Status |
| --- | --- | --- | --- |
| Squaring a Boolean-weighted sum | `JointSourceExpansion.weighted_square` | `CommRing F`, `2=0`, every weight idempotent | Kernel checked |
| Cubing the sum | `JointSourceExpansion.weighted_cube` | Same; exact recursive singleton and pair formula | Kernel checked |
| Fourth power | `JointSourceExpansion.weighted_fourth` | Same; exact linear fourth-power formula | Kernel checked |
| Joint cubic term | `JointSourceExpansion.joint_cubic_rewrite` | Two Boolean-weighted sums with separate idempotence hypotheses | Kernel checked |
| Every exponent from zero through four | `JointSourceExpansion.source_power_correct` | Same and explicit supported-exponent disjunction | Kernel checked |
| Full polynomial rewrite | `JointSourceExpansion.joint_resultant_expansion` | Same; each term's two exponents lie in `0..4`; arbitrary coefficient list | Kernel checked |

The pinned toolchain is `leanprover/lean4:v4.34.1` in
[lean-toolchain](lean-toolchain). `lean JointSourceExpansion.lean` built
the actual module. [lean_check.log](lean_check.log) includes the
`#print axioms` output for every declaration; each lists only
`propext`, `Classical.choice`, and `Quot.sound`. The source contains no
`sorry`, `admit`, `sorryAx`, custom axiom, `unsafe`, native evaluation,
or kernel bypass. `lean4checker --fresh` is unavailable here.

The explicit ANF *support-degree predicate* and its connection to
`joint_gb.py` are not yet formalized in Lean. The checked rewrite
identifies the exact expansion; the source-family degree bound follows
from the displayed recursive formulas, and the producer computes and
checks every emitted monomial's first- and second-family popcount.
For N41, it also compared the resulting ANF to direct field evaluation
on every assignment in each tested block. For N131, the constructed
positive assignment was checked against the direct frozen resultant.
The formalization of the support predicate and code-level refinement
is partial and remains a separate proof obligation.
