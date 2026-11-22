# Proof map for source-addition linear span

| Result | Lean declaration | Hypotheses and verification |
| --- | --- | --- |
| The first 48 raw-x error vectors XOR-generate every standard basis vector at bits 1 through 40 | `NearCharacterRank.certificateX` | The concrete 48 decimal vectors and 40 explicit XOR witness lists are in `NearCharacterRank.lean`; Lean 4.34.1 checks each equality by kernel reduction. |
| The first 48 reciprocal-x error vectors have the same basis coverage | `NearCharacterRank.certificateInverse` | Same concrete construction and checked proof for the independent coordinate law. |
| A binary-linear test that vanishes on the named raw-x errors vanishes on all 40 nonconstant basis directions | `NearCharacterRank.no_extra_linear_equalityX` | Requires `test(0)=false`, XOR-linearity of `test`, and `test=0` on the named 48 error vectors. It does not assume the basis conclusion. Checked. |
| The corresponding implication for reciprocal-x errors | `NearCharacterRank.no_extra_linear_equalityInverse` | Same exact hypotheses and checked proof. |
| The 48 named vectors are the declared curve-law errors from the archived N41 pair states | Checked-Sage `audit.json` | The audit independently reconstructs the first 128 training vectors from curve points, including all 48 Lean rows. This concrete curve arithmetic is not yet formalized in Lean. |
| Any exact linear equality on the full source law is constrained by the sampled errors | Immediate subset implication | Every sampled error is a valid source-law error by the group audit. An equality on the full source must hold on these 48; the checked theorems then force its values on all 40 nonconstant basis directions. |

Build from this directory with `lean NearCharacterRank.lean`; the pinned toolchain is in `lean-toolchain`, the compiler version in `lean_version.txt`, and `#print axioms` output in `lean_check.log`. The standard foundations reported are `propext` and `Quot.sound`. The failed initial build and repaired source are retained. `lean4checker --fresh` could not be run because the command was unavailable. The remaining formal bridge is the exact N41 curve-law construction of the 48 integer error vectors; its independent Sage replay is the present concrete evidence.
