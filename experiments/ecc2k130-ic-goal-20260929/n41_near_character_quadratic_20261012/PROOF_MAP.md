# Proof map for quadratic source-addition rank

| Claim | Declaration or evidence | Status and assumptions |
| --- | --- | --- |
| A Boolean XOR-linear test vanishing on a sample also vanishes on its XOR span | `QuadraticStructural.linear_zero_on_xorSum` | Checked in pinned Lean 4.34.1; assumes `test(0)=false`, XOR-linearity, and vanishing on the named sample list. |
| If all 821 feature-basis vectors have sampled XOR witnesses, any such test vanishes on every feature direction | `QuadraticStructural.sampled_basis_forces_linear_zero` | Checked structural theorem. The witness equalities and membership are explicit conditional hypotheses, not an assumed conclusion. `structural_check.log` contains `#print axioms`. |
| The first raw-x feature-basis vector has the archived XOR witness | `QuadraticChunkX00.certificate` in `QuadraticFirst.lean` | Kernel checked under a 45 s/4 GiB cap; `first_basis_stdout.log` reports only `propext`. |
| All 821 raw-x and 821 reciprocal feature-basis vectors have archived XOR witnesses | `certificate.json`, `verification.json` | Independent Python low-pivot elimination verifies every equality and binds the 821 selected rows to the archived vectors. The full Lean data theorem is **open**: its 4-GiB run was stopped, and the first 32-case chunk reached 2 GiB. The remaining 1,641 equalities require a more compact kernel certificate. |
| The selected feature rows derive from the declared N41 diagonal source additions | `audit.json` | Checked Sage independently reconstructs the first 825 source errors, including all selected rows. This finite curve-law replay is not formalized in Lean. |
| No degree-at-most-two Boolean polynomial on nonconstant error bits vanishes on the entire source law unless its coefficient vector is zero | Written proof in `RESULT.md` | Follows from full rank of a valid source subset and the exact monomial feature encoding. The mathematical conclusion is computationally certified; faithful complete Lean formalization remains partial for the concrete 821-basis premise and curve-law bridge. |

The pinned `lean-toolchain` is `leanprover/lean4:v4.34.1`. The checked structural theorem and checked first concrete equality report only standard `propext`. Failed and capped Lean runs remain separate receipts and are not cited as proofs. `lean4checker --fresh` was not available.
