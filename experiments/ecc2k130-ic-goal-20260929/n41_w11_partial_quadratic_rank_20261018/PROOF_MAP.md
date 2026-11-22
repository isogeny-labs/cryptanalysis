# Proof map: quadratic feature-span exclusion

Let `S` be the exact raw two-pair right-partial family specified in
[RESULT.md](RESULT.md). For each reciprocal coordinate `x`, let `φ(x)`
contain the constant, 41 linear, and 820 squarefree quadratic Boolean
monomials. A coefficient vector `c` represents a unique degree-at-most-two
Boolean polynomial `P_c(x)=c·φ(x)`.

The independently replayed witness matrix has 862 rows and rank 862 over
`GF(2)`. If `P_c` vanishes on all of `S`, it vanishes on those rows. Their
span is the whole 862-dimensional feature space, so the linear test
`v ↦ c·v` vanishes everywhere. Evaluating on standard basis vectors gives
`c=0`. This proves the stated exclusion for this exact family, without an
assumption about unobserved partial sums.

| Result | Formalization and exact status |
| --- | --- |
| A binary-linear test vanishing on a spanning sample vanishes on every `width`-bit feature vector | `FullFeatureRank.full_span_forces_zero_test` in [FullFeatureRank.lean](FullFeatureRank.lean); Lean 4.34.1 kernel checked. Its `span_within` premise ranges over `v < 2^width` and is the full-span statement, not the conclusion that the test vanishes. Here `width=862`. |
| XOR linearity of evaluations over a selected sample | `FullFeatureRank.linear_test_zero_on_xor_sum`; Lean 4.34.1 kernel checked. |
| Concrete N41 witnesses lie in `S` and span `GF(2)^862` | [result.json](result.json), [verify_result.json](verify_result.json); independently replayed integer-field group law and separate Boolean pivot implementation. The numeric certificate and source-to-feature bridge are not yet encoded in Lean. |
| Unique coefficient representation of squarefree Boolean polynomials | Readable proof above; Lean bridge from 862 bit positions to degree-at-most-two monomials remains open. |

The actual module uses pinned [Lean 4.34.1](lean-toolchain);
`lean FullFeatureRank.lean` succeeded. [lean_check.log](lean_check.log)
records `#print axioms` with only `propext` for both declarations. The
module has no `sorry`, `admit`, custom research axiom, or native-evaluation
proof step. `lean4checker --fresh` was unavailable on this host.
