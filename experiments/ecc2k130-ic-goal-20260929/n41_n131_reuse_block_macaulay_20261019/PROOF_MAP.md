# Proof map

The row family and certificate meaning are unchanged from the [trace experiment](../n41_n131_trace_block_macaulay_20261019/PROOF_MAP.md). The code change replaces a newly allocated symmetric-difference output vector with a cleared reusable vector, then swaps it with the current row. For sorted input supports `A` and `B`, both implementations compute the same parity support `A △ B`.

| Result | Declaration or check | Status |
| --- | --- | --- |
| Constant-one equation-multiple identities exclude simultaneous zeros | `../n41_w11_block_macaulay_20261019/BlockCertificate.lean`: `constant_one_block_certificate_sound` | Previously checked Lean 4.34.1 theorem; no mathematical statement changed in this experiment. |
| Five N41 identities and retained positive block | `verify_n41.py`, six receipts, five `CERT_ROWS` logs | Exact original-row supports replay to `{0}` for every exclusion; the known-root block remains `UNRESOLVED_AT_DEGREE6`. |
| N131 prefix | `verify_n131.py`, positive receipt and progress log | The frozen 120-second cap produced a censored prefix, with the public block gated. |

The concrete field arithmetic and all input coefficient supports were independently audited by checked Sage in the sparse experiment, whose result hash is included in both protocols. A Lean model of the compiled reducer and exact field encoding remains open; the active mathematical theorem concerns certificate soundness, while these producer checks establish the concrete inputs and emitted identities.
