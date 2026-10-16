# Torsion-paired S3 proof map

The new four-preimage query uses the same quadratic algebra for two public
targets related by the rational two-torsion point `(0,1)` on
`y²+xy=x³+1` over `GF(2^131)`.

| Mathematical step | Lean declaration | Exact hypotheses and status |
| --- | --- | --- |
| Adding `(0,1)` sends a nonzero affine `x` to its inverse | `TorsionCoordinate.torsion_add_x_inverse` in `../n131_w20_paired_raw_quotient_20261016/TorsionCoordinate.lean` | Field of characteristic two, curve equation, chord-slope and addition formulas, `x != 0`; checked in the predecessor artifact |
| Inverting a right S3 coordinate and target coordinate preserves the S3 zero set | `TorsionS3.reciprocal_identity`, `TorsionS3.reciprocal_root_iff` | Commutative ring with explicit inverse witnesses for identity; field for zero-set equivalence; checked here |
| A nonzero right root's inverse is affine in that root modulo its quadratic | `TorsionS3.inverse_linear` | Commutative ring of characteristic two, right quadratic equation, explicit inverse witness; checked here |
| Original and torsion-partner right products share the same quadratic-algebra denominator | `TorsionS3.fused_initial` | Same hypotheses as `inverse_linear`; checks both initial affine numerator pairs; checked here |

The pinned toolchain is `leanprover/lean4:v4.34.1` in `lean-toolchain`.
`lean TorsionS3.lean` produced the saved `lean_output.txt` with four
`#print axioms` entries containing only `propext`, `Classical.choice`, and
`Quot.sound`. The module has no `sorry`, `admit`, custom axiom, or native
evaluation. `lean4checker` was unavailable on this host.

The complete bridge from the predecessor chord formulas to the concrete Sage
curve point type remains outside these new declarations. The frozen
`target_preimages.json` records the four public points. The runner verifies
their reciprocal-chart conversion and the two inverse target pairs in the
accepted field; the 128-code sample compares 512 derived partner root sets
against independent direct quadratic solves. The native full scan checks
source membership and caps separately. These checks are the concrete bridge
for this experiment, and the Lean curve-point bridge remains a formalization
task.
