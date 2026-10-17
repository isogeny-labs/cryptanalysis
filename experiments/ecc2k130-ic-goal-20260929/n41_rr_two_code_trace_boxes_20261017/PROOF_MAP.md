# Proof map

| Result | Proof or evidence | Status |
| --- | --- | --- |
| A trace polynomial equal to one at a determinant excludes determinant zero. | `QuadraticTrace.separator_excludes_zero` in `../n41_n131_rr_quadratic_trace_20261017/QuadraticTrace.lean`; Lean 4.34.1 `#print axioms` reports standard `propext` only. | Checked structural theorem, reused without revision. |
| The lexical 1,024-state box has no shared certificate from the first 24 odd powers but has one from the first 25. | Exact feature/augmented ranks in `result.json`; independently recomputed at 24 and 25 in `audit_result.json`; explicit 25-coefficient field vector in `certificate.json`, independently checked against all Sage determinants in `certificate_audit_result.json`. | Checked finite instance. |
| The Boolean ANF, finite-field trace-pairing and seven-point curve determinant bridge. | Written derivation in the preceding experiment's `RESULT.md` and its `PROOF_MAP.md`; checked-Sage determinant and trace replays here. | Lean formalization partial; exact bridge remains open. |

The rank-24 obstruction covers every shorter prefix because setting all new
coefficients to zero embeds any shorter certificate into the 24-power system.
No curve-level theorem or asymptotic complexity claim is inferred from the
ordinary-host cost screen.
