# Proof map: target fingerprint in a two-code quotient

The exact construction uses the coefficient ring

`R = GF(2^41)[p,q]/((p+p₀)(p+p₁), (q+q₀)(q+q₁))`.

For a complete 2×2 code rectangle, evaluation of `R` at each of its four
code pairs is well defined. Specializing the archived degree-eight
`H(a,b,p,q,U)` **once in `R`** gives the 32-dimensional algebra `R[U]/H`.
The producer checks that the leading coefficient of `H` and `H(1)` are
units in `R`. It then represents `z=1/x=U/(1+U)` and every selected
absolute-trace bit of `z` in that quotient.

For target bit `tᵢ`, the factor `bᵢ(z)` if `tᵢ=1`, or `1+bᵢ(z)` if `tᵢ=0`,
evaluates to one exactly when bit `i` matches. Their product `Iₖ` equals
one at a root exactly when its first `k` bits match the public residual.
If `Iₖ=0` in the quotient, the entire code rectangle is excluded. Once
zero, every later product remains zero, allowing early stopping.

| Result | Lean declaration or finite check | Status |
| --- | --- | --- |
| Boolean equality product is one exactly when every selected bit matches. | `QuotientFingerprint.indicator_true_iff_all_equal` in `FingerprintSound.lean` | Checked under all finite Boolean pair lists. |
| Zero indicator excludes an exact bit match. | `QuotientFingerprint.indicator_zero_excludes_exact` | Checked without custom axioms. |
| A zero partial indicator remains zero after more bits. | `QuotientFingerprint.zero_persists` | Checked without custom axioms; justifies early stopping. |
| The two-axis coefficient quotient, H specialization, chart conversion, and fingerprint residues agree at the actual N41 roots. | `audit_hash_sage.py` | Independently checked for 132 rectangles, 528 code pairs, 4,224 roots, 4,752 specialized H coefficients, and 16,896 checkpoint evaluations. |

The Lean module is pinned to `leanprover/lean4:v4.34.1` with bundled `Std`.
`lean_check.log` retains the build and `#print axioms` results: `propext`
and `Quot.sound` for the first two theorems, `propext` for the third.
The formalized Boolean implication has a readable induction proof in the
module. A faithful polynomial-quotient formalization of `GF(2^41)`, code
annihilator ideals, and the trace-dual embedding is still open; the Sage
audit verifies this concrete finite bridge. The earlier
`n41_quotient_trace_cubic_20261023/PROOF_MAP.md` records the checked
conditional quotient-constant soundness theorem and the unavailable
Mathlib dependency needed for a direct polynomial-syntax proof.
