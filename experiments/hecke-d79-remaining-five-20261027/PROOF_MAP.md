# Proof map for the five-prime rank panel

For each `p` in `3797, 8237, 8597, 12197, 12637`, `p<p>/formal/RankP<p>.lean` contains explicit row matrices for base plus direct, base plus Hecke, and base plus both arms. Every module is generated from the hash-pinned producer receipt and independently audited analysis by `p<p>/formal/generate.py`. The module's `#print axioms` commands audit the checked declarations. Toolchain: `leanprover/lean4:v4.35.0-rc4`, no external dependency. Build each module from its `formal/` directory with `lake build RankP<p>`; retained output is `build-output.txt`. `lean4checker --fresh` is unavailable on this host.

| Result | Lean declaration family | Exact inputs and status |
| --- | --- | --- |
| All rows in each arm annihilate the displayed nonempty kernel vectors over `F_q` and over `Z` | `RankP<p>.<arm>_all_rows_annihilate_q_kernels`, `<arm>_all_rows_annihilate_z_kernels` | Checked finite enumeration over the explicit 40-column matrices. Integer-kernel declarations are emitted only when the rational rank is below 40. |
| Displayed kernel vectors are independent on their free coordinates | `RankP<p>.<arm>_q_kernels_free_identity`, `<arm>_z_kernels_free_diagonal`, `<arm>_z_kernels_diagonal_nonzero` | Checked finite-coordinate identities for each nonempty kernel basis; integer declarations are omitted at rational rank 40. |
| Selected rows belong to the full arm matrix and have an invertible minor | `RankP<p>.<arm><modulus>_rows_in_all`, `_minor_matches`, `_inverse_certificate` | Checked modulo `q` and an auxiliary prime. The auxiliary prime is 7 for `p=8597`, 3 otherwise. |
| The table's exact row ranks over `F_q` and `Q` | The declarations above are the finite certificates; the mathematical proof uses the standard rank bounds from independent kernels and invertible minors. | **Partial formalization:** the general linear-algebra implication from certificates to a Lean matrix-rank equality is not yet encoded. The complete Sage rank is independently replayed in `audit.json`. |
| Each generated row is an actual curve relation | No Lean curve declaration yet. | **Partial formalization:** the finite-field Weierstrass model, 40 class points, degree-13 fiber lifts, trace sums, and the bridge from the Sage checked rows to the Lean matrices remain to be encoded. `audit_sage.py` replays every row on the curve; `audit_q_logs_sage.py` checks the projected subgroup logs. |

The mathematical rank argument is explicit. An invertible `r×r` minor among selected rows gives rank at least `r`. For rank less than 40, the displayed `40−r` integer or `F_q` kernel vectors are independent by their free-coordinate diagonal and annihilated by every row, so rank is at most `r`. For rational rank 40, the auxiliary-prime invertible minor already gives both bounds. This argument applies to the exact matrices in the generated declarations; formalizing the general implication and curve bridge is the remaining work.

## Retained generation correction

The first `p8597` generator run failed before emitting a Lean module: a broad auxiliary-prime substitution changed the JSON key `degree13_sources` to `degree17_sources`, raising `KeyError: 'degree17_sources'`. The key was restored, the module regenerated, and `formal-generation-check.txt` records a passing exact regeneration check for all five modules. No failed module was reported as checked.
