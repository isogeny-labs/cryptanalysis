# Proof map for the five-pair W9/W29 topology

| Mathematical statement | Lean declaration | Exact hypotheses and status | Concrete bridge |
| --- | --- | --- | --- |
| Four balanced links sum the five pair points | `FivePairJoin.balanced_five_sum` | Any `AddCommGroup`; checked with no axioms | N41 Sage replay sums the five reconstructed rotated pairs; N131 constructed assignment checks the four S3 links. |
| The three-plus-two addition tree also sums the five pair points | `FivePairJoin.balanced_three_two_sum` | Any `AddCommGroup`; checked with no axioms | The second N131 constructed assignment checks the three-plus-two S3 links on the same five source pairs and same raw target. |
| Three-left/two-right lookup is exact | `FivePairJoin.target_conditioned_lookup` | Any `AddCommGroup`, all `left`, `right`, `target`; checked with no axioms | Native worker computes `target-right`, then checks each hit with its independent group addition code; Sage replays the selected relation. |
| An additive inverse map transports a Frobenius-orbit hit to the original target | `FivePairJoin.orbit_transport` | Any `AddCommGroup`; maps `f,g`, hypotheses `g(f(x))=x` and additivity of `g`; checked with no axioms | Sage squares both coordinates for the selected orientation and for its inverse, then checks exact raw and subgroup targets. The finite-field Frobenius group-homomorphism bridge is checked computationally here, not formalized in Lean. |
| Fixed-seed pair-output law and shared product inverse | Existing `OutputLinearization.pair_output_linear_iff` and `SharedInverse.product_inverse_gives_endpoint_inverses` | Characteristic-two ring with inverse witness; prior checked modules | N131 five-pair constructed control checks every emitted CNF clause and XOR row; independent Sage reconstructs source-valid pairs. |

The checked module is `FivePairJoin.lean`; `lean-toolchain` pins
`leanprover/lean4:v4.34.1`. Run `lean FivePairJoin.lean` from this directory.
`lean_v2.stdout` records all four `#print axioms` checks; none depends on an
axiom. No `sorry`, `admit`, custom axiom, or native-evaluation proof appears.

The native N41 source census, joined state counts, and deterministic W29
sample are finite computations. The Sage replay is a separate implementation
check of the N41 field, curve, source masks, point signs, Frobenius maps,
columns, and public point. The W29 sample is not an exact count of all
width-29 source edges. A solver SAT model would require the independent Sage
group and column audit before becoming an ordinary relation.
