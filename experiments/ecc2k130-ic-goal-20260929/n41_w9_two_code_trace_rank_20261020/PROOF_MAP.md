# Proof map

| Statement | Lean declaration or finite check | Status |
| --- | --- | --- |
| The degree-at-most-two Boolean code monomials times `(1,z₀,…,z₄₀)` give 5,754 features | `TwoCodeTraceRank.feature_count` | Checked Lean 4 |
| `left < right` forces `left_bit7 · (1+right_bit7)=0` | `TwoCodeTraceRank.ordered_top_bit_gate`; exact code rows in `verify_retry.py` | Checked Lean 4 and exhaustive finite rows |
| Full feature rank excludes every nonzero universal predicate in this feature space | `TwoCodeTraceRank.full_rank_sample_excludes_filter` | Checked Lean 4 under explicit full-span hypothesis |
| The ordered code-only monomials have rank 136/137 and unique top-bit relation | Independent low-pivot `verify_retry.py`; high-pivot producer and the displayed relation | Exact finite computation; concrete pivot certificate is outside Lean |
| Ordered output features have rank 5,712/5,754; both orientations reach 5,754/5,754 | High-pivot producers and independent low-pivot replay | Exact finite computation, full-rank bridge supplied by replay |
| All 39,712 reciprocal outputs equal the exact N41 group-sum x coordinate | Checked Sage producer and separate explicit affine-addition audit | Independent arithmetic replay on pinned field/curve |

The readable proof of the rank implication is linear algebra over `GF(2)`:
any predicate of the stated form is a binary dot product with one
5,754-bit coefficient vector. If it vanishes on rows spanning the entire
feature space, that vector is zero. The single ordered-domain code
relation `left_bit7(1+right_bit7)` has 42 independent multiples by the
constant and 41 output coordinates. The measured rank deficit is exactly
42, so these account for the complete ordered-domain nullspace. The
reversed families break that ordering condition and close the rank.

`TwoCodeTraceRank.lean` pins `leanprover/lean4:v4.34.1` and builds with
`lean TwoCodeTraceRank.lean > lean_check.log 2>&1`. Its `#print axioms`
output reports only `propext` and `Quot.sound` for the structural
declarations. There are no `sorry`, `admit`, custom claim axioms,
unverified native proofs, or kernel bypasses. The exact field encoding,
curve arithmetic, and finite pivot rows are verified by the paired
executables, not formalized as Lean data. Full Lean formalization would
need a compact kernel-checkable rank certificate and a formal bridge
from the exported finite-field words to its feature rows.
