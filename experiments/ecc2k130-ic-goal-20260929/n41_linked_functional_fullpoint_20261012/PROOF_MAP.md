# Proof and replay map

| Claim | Evidence | Exact scope |
| --- | --- | --- |
| Reused Frobenius source pair folds its two columns by `1+λ⁷` | [Prior Lean theorem and proof map](../n41_n131_linked_frobenius_pair_20261012/PROOF_MAP.md) | The checked generic factorization and prior Sage subgroup/order audit apply to this exact linked source. |
| V3 full-point links reproduce the known ten signed pair points | [Control model](v3/control.json), [prior independent Sage relation](../n41_n131_linked_frobenius_pair_20261012/audit_result.json), [verifier](verify.py) | The selected state IDs and raw preimage match the prior independently replayed relation; all nine emitted addition links and all control XCNF rows check. |
| Unpinned public solver status | [Public receipt](v3/public.json), [raw log](v3/public.stdout), [verifier](verify.py) | One worker, 180-second parent cap, 4-GiB combined RSS; no SAT/UNSAT terminal line. |
| Failed first producer and recovered second control | [Failure audit](failure_audit_result.json), [v2 recovery](v2/recover_result.json) | Parser rejection is classified separately from search. The v2 saved SAT model passes independent row and group replay after correcting the decoder. |

This experiment adds an implementation and measurement result to the existing linked-source construction; it introduces no new mathematical theorem. The full binary-field/curve formalization bridge remains recorded in the prior linked-pair proof map and in the functional full-point circuit's proof map.
