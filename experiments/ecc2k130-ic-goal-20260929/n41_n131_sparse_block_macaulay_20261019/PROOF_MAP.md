# Proof map for sparse block certificates

Let `E_i(x)` denote the exact Boolean field-coordinate equations of a frozen target-conditioned eliminant, and let `m_j(x)` be any Boolean code-bit monomial of degree at most two. If a subset of the rows `m_j E_i` XORs to the constant polynomial one in the Boolean quotient, then no Boolean assignment can solve every `E_i=0`. At any common zero, every selected multiple evaluates to zero while the constant evaluates to one.

| Result | Declaration or check | Status |
| --- | --- | --- |
| Soundness of a constant-one combination of equation multiples | `../n41_w11_block_macaulay_20261019/BlockCertificate.lean`: `constant_one_block_certificate_sound` | Checked with Lean 4.34.1. Its arbitrary multiplier and commutative-ring hypotheses cover the sparse row products; `#print axioms` reports standard `propext`, `Classical.choice`, and `Quot.sound`. The theorem and existing proof are unchanged here. |
| Exact source-to-equation expansion | `audit_inputs_sage.py`, `audit_result.json`, and eight `.eqs` inputs | The checked Sage runtime independently reconstructed all 41 or 131 field-coordinate ANF supports and matched each input file. The audit protocol hashes runtime, script, source inputs, and expected equation files. |
| Five N41 exclusions | Five `REJECT_CERTIFICATE` logs and `verify_n41.py` | The read-only verifier replayed the recorded row ID combinations and obtained exactly the constant-one support `{0}` for each. The prior N41 archive independently checked the same block outcomes against all 24,576 assignments. |
| N41 retained public-relation block | `n41_t0_a252.stdout`, prior N41 relation replay | All 3,239 rows were processed without a constant-one combination; the preceding archive independently located the root `(253,63)` in this block. |
| N131 degree-six prefix | `n131_t0_a0.stdout`, `n131_t0_a0.receipt.json` | The positive control reached `WALL_CAP` after a last checkpoint at 17,000 rows. No constant-one identity or full-span result was produced; the public block was gated. |

The Lean theorem proves the structural implication from a valid identity, while independent executable checks establish concrete identities and source coefficients. A bit-level Lean model of these concrete finite-field encodings remains open. The cap status is a finite execution boundary and supplies no mathematical exclusion of the N131 block.
