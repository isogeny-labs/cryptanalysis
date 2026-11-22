# Affine recovery of the N131 right pair product

The full N131 W20 two-pair source scan recovered the right product directly
from each target S3 root using a 19-dimensional binary basis inverse. It
agreed with the earlier right-root hash oracle on every candidate of both
frozen queries: one distinct-column constructed hit at codes `(3,16722)`
and zero two-pair hits on the ordinary raw public point. The independent
audit checked the affine identity on all **1,056,360** S3 roots.

For target S3 coefficients `A=1+(ct)^2`, `B=ct`, `D=c^2+t^2`, the right pair
law is `C d^2+p d+H=0`. On the `D != 0` chart,

`p = (C+H A/D)d + H B/D`.

The implementation batches inverses of all nonzero `D` values and recovers
`p` through a high-pivot basis. The archived
[batched quadratic-algebra oracle](../n131_w20_batched_quadratic_20261017/RESULT.md)
already used this affine identity in a 19-step span recurrence; this run
quantifies direct product-code recovery and supplies a full-candidate
cross-check for the subsequent
[code-linear solve](../n131_w20_code_linear_right_20261017/RESULT.md).

The [producer protocol](protocol.json) fixes the `GF(2^131)` modulus
`t^131+t^13+t²+t+1`, W20 seed mask 898618, Frobenius rotation 18, exact
fixture, support/validity files, source/binary hashes, one worker, 590-second
native cap, 600-second parent cap, and 4 GiB RSS. The [native result](native_result.json)
records 132,045 valid codes, 264,090 left roots, 528,180 S3 roots per
query, zero exceptional denominators, 4.703 seconds setup, 12.908 seconds
constructed query, and 12.226 seconds ordinary query. The [parent
receipt](receipt.json) records 30.128 seconds wall, 44,924,928 bytes
sampled combined RSS, exit zero, and no monitor failure.

The separate [audit](audit_result.json) rebuilt the right-root index and
used a low-pivot basis with direct inversion at each S3 root. It found exact
hit equivalence for both targets and affine/direct product equality on all
1,056,360 roots. Its [receipt](audit_receipt.json) records 46.187 seconds
parent wall, 68,665,344 bytes sampled combined RSS, and PASS within the
same caps. The [proof map](PROOF_MAP.md) identifies the checked Lean
statements and their exact nonzero-denominator hypotheses.

This complete two-pair component retains `candidate_id: null`. The code-bit
linear method in the linked experiment uses the affine identity to reject
an entire right-source code span before extracting S3 roots.
