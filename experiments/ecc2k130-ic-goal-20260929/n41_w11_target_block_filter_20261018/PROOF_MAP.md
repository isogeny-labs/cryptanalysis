# Proof map

`BlockSpanSoundness.rejected_family_has_no_allowed_member` proves the
structural implication used by the diagnostic. Its quantified family is the
set of target-conditioned second source products from one first-code block.
The `directions` predicate denotes the XOR span of differences from the
block's first product; `allowed` denotes the rotated source-product subspace.
The hypothesis `enclosure` requires every family member to lie in that
affine span. When all affine points fail `allowed`, every exact family member
fails it. The checked Sage experiment computes the finite family and its
span explicitly; those concrete finite calculations are outside Lean.

`BlockSpanSoundness.full_direction_space_prevents_rejection` proves that
the predicate cannot reject once directions cover all 41-bit vectors and
zero is allowed. This formalizes the full-rank diagnostic. It does not
equate a rank below 41 with rejection.

Toolchain: `leanprover/lean4:v4.34.1` from `lean-toolchain`.
Command: `lean BlockSpanSoundness.lean > lean_check.log 2>&1` in this
directory. `#print axioms` is in the module. The declarations use only
Lean's standard `propext` and no custom axioms, `sorry`, or native evaluation.
The source-product identity and exact point arithmetic are covered by the
prior [checked theorem and independent group audit](../n41_w11_exact_two_pair_oracle_20261018/PROOF_MAP.md).
