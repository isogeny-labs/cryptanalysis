# Proof map for dependency-traced certificates

Write the original equation-multiple rows as `R_k=m_j E_i` over the Boolean quotient. Every saved pivot `P_t` records an original row ID `k_t` and a list of earlier pivot indices `D_t` such that `P_t=R_{k_t}+Σ_{u∈D_t}P_u`. This invariant follows by induction over the reducer's strictly earlier pivot references. When a current row reduces to the constant one, toggling its original row and traversing included pivot dependencies in descending index order reconstructs a set of original rows whose XOR is one. The implementation prints only the rows of odd parity.

| Result | Declaration or finite check | Status |
| --- | --- | --- |
| A constant-one sum of equation multiples excludes simultaneous zeros | `../n41_w11_block_macaulay_20261019/BlockCertificate.lean`: `constant_one_block_certificate_sound` | Checked Lean 4.34.1 theorem with arbitrary multipliers and explicit ring/nontriviality assumptions. The existing module's `#print axioms` reports only standard foundations. |
| Dependency reconstruction for emitted N41 certificates | `trace_block.cpp`, five `CERT_ROWS` logs, `verify_n41.py` | The read-only verifier XORed the original coordinate-equation supports selected by each emitted certificate and obtained exactly `{0}` in every case. This independently checks the concrete reconstruction outputs. |
| Input polynomial and field correspondence | Prior `n41_n131_sparse_block_macaulay_20261019/audit_inputs_sage.py` and its completed audit, hashed by both query protocols | All eight coordinate support files were reconstructed from checked Sage finite-field arithmetic in the preceding archive; this experiment uses the same hashed files. |
| N131 positive control | `n131_t0_a0.receipt.json`, `n131_t0_a0.stdout`, `verify_n131.py` | The reducer reached `WALL_CAP` after its 17,000-row progress checkpoint. No terminal certificate or complete-span assertion follows from the prefix. |

The Lean theorem proves the structural consequence of a valid identity. The dependency invariant is proved above at the algorithm level, and the emitted identities are independently replayed. A Lean formalization of the exact C++ trace transition and the concrete finite-field representation remains open.
