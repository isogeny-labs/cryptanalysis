# Proof map for the nonzero branch and W33 audit

| Result | Formal declaration or check | Hypotheses and status |
| --- | --- | --- |
| `pF=0 ↔ F=0` on a nonzero first product | `DegreeFall.scaled_zero_iff` in [DegreeFall.lean](../resultant_degree1_syzygy_20261019/DegreeFall.lean) | Any field and `p≠0`. Checked with Lean 4.34.1; `#print axioms` reports `propext`, `Classical.choice`, `Quot.sound`. |
| The scaled resultant has Boolean degree at most three | `DegreeFall.scaled_support_degree`, `DegreeFall.fourth_additive`, and `DegreeFall.binary_bit_fourth` in the same module | Exact 13-term support, characteristic two, idempotent code bits. Checked Lean theorem for the support bound and abstract power identities; concrete quotient-field ANF multiplication is a finite computational bridge. |
| Odd first-code branch has nonzero `p` | `branch_gb.py` finite eight-product check in both N131 runs | Exact W33 seed `898618`, source-bit map, rotations, and codes `0..15`. Computationally checked; no independent Lean theorem for the concrete 131-bit source representation. |
| GCD degree zero rejects every second product in W33 | `w33_gcd_audit_sage.py`, [32-row result](w33_gcd_result.json) | `L_V` vanishes on the complete rank-32 product basis; for each specialized quartic, a common W33 root implies nonconstant GCD. Exact Sage polynomial arithmetic. The polynomial Bézout bridge to the concrete Sage representation is not formalized in Lean. |
| Degree-one GCD yields the positive second code and curve-point sum | `w33_direct_root_sage.py`, [direct result](w33_direct_root_result.json) | Full-rank `131×32` binary basis, recovered root satisfies both polynomials, code re-encodes to the root, and one sign choice sums to the frozen constructed point. Exact checked-Sage computation; prior independent replay is also hash-bound. |
| All finite-block and resource receipts refer to frozen inputs | `verify_terminal.py`, [terminal receipt](verification_result.json) | Hashes 42 source artifacts, exact statuses, code values, protocol digests, caps, and checked launcher command. Corrected version passes after a preserved first schema mismatch. |

The earlier `DegreeFall.lean` module is pinned to
`leanprover/lean4:v4.34.1`; its build and axiom-audit output are in
[lean.stdout](../resultant_degree1_syzygy_20261019/lean.stdout).
`lean4checker --fresh` was unavailable on this host. The full statement
connecting the concrete N131 quotient-field encoding, exported resultant,
source-code product map, GCD computation, and elliptic-curve point replay
remains a computationally checked bridge rather than a single Lean theorem.
