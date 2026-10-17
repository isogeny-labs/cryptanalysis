# Proof map

| Mathematical result | Lean declaration | Exact hypotheses | Status |
| --- | --- | --- | --- |
| A shared trace polynomial equal to one excludes every zero determinant in its covered sign domain. | `QuadraticTrace.separator_excludes_zero` | An arbitrary `CommSemiring F`, sign type `S`, trace map with `trace 0 = false`, two coefficients, and an explicit certificate equality for every sign. | Checked; `#print axioms` reports only `propext`. |
| A witnessed zero blocks any shared quadratic certificate. | `QuadraticTrace.witnessed_zero_blocks_separator` | Same semiring and trace assumptions plus one sign with determinant zero. | Checked; `#print axioms` reports only `propext`. |
| The Boolean ANF coefficient identity for `D³`, exact 64-equation trace characterization, nondegenerate trace pairing in the specific binary fields, and the bridge to the seven-point determinant. | Open | Requires a finite Boolean-mask algebra, characteristic-two field, polynomial-basis field construction, and determinant encoding. | Written proof and independently checked finite computations in `RESULT.md`, `audit_sage.py`, `audit_odd_sage.py`, and `verify_odd_cert_sage.py`; Lean formalization partial. |

Build command from this directory: `lean QuadraticTrace.lean > lean.stdout 2> lean.stderr`.
Toolchain: `leanprover/lean4:v4.34.1` in `lean-toolchain`.
