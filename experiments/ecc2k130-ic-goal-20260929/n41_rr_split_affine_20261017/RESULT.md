# Split-minor target certificate on frozen N41 source boxes

**A 35-coordinate left/right minor factorization preserves the exact
public-target determinant and its 32 fixed-sign rejection
certificates.** On the frozen source panel it gives no additional
whole-family rejection: all tested root and code boxes reach full
41-bit determinant-difference rank. The 69-box worker completed in
25.827 s with 3,223,177 charged field multiplications; an independent
Gaussian-determinant audit replayed 3,664 assignments and the one
recorded positive witness.

The [proof map](PROOF_MAP.md) derives the split. For each source triple
form 35 three-row minors (L); for each remaining triple together
with (-Q), form the complementary 35 four-row minors (R). The
seven-row public-target determinant is their bilinear dot product.
A binary-linear functional that is one on the base pairing and zero
on every left, right, and cross difference certifies that an entire
Cartesian family misses the target. The checked Lean theorem proves
this affine bilinear implication under explicit bilinearity and
annihilation hypotheses.

## Frozen N41 screen

The instance is `EC1N41Ckb1h7d5e80d3c4d0` over
`GF(2)[t]/(t^41+t^3+1)`, with six fixed-seed W8 source slots and
their signed point states. The raw public target and source hashes
come from the prior [RR box panel](../n41_rr_joint_box_rank_20261017/RESULT.md).
The [protocol](protocol.json) selected 32 sign boxes, four
root-and-sign boxes, 32 two-code boxes, and the witness-containing
two-code box before split-minor evaluation. It fixed one worker,
180 s and a 4-GiB observational RSS boundary.

| Frozen box family | Boxes | Split classifications | Pairings evaluated | Direct determinants in independent replay |
| --- | ---: | --- | ---: | ---: |
| Fixed sign | 32 | 32 certified no zero | 2,048 | 2,048 |
| Root and sign | 4 | 4 full-rank, no affine separator | 175 | 175 |
| Two code | 32 | 32 full-rank, no affine separator | 1,410 | 1,399 |
| Witness two code | 1 | Full-rank, witness retained | 42 | 42 |
| **Total** | **69** |  | **3,675** | **3,664** |

Every fixed-sign box has left/right minor-vector difference ranks
7 and 7 and determinant-difference rank 34. Its split expansion
requires all (1+7+7+49=64) pairings, so this implementation does
not reduce the number of pair evaluations for those certificates.
The broader boxes reach rank 41 before their Cartesian products are
exhausted; that is an obstruction to this *single linear functional*,
not a classification of unvisited assignments. The frozen positive
control has base determinant zero, and the independently replayed
ordinary witness remains present.

The worker's [raw result](result.json) reports 25.827 s and
24,870,912 B peak self RSS. It computed 3,223,177 field
multiplications, including minor-vector construction and pairings.
The [independent auditor](audit_result.json) used separate carryless
multiplication, Euclidean inversion, and seven-row Gaussian
elimination. It checked every fixed-sign certificate against all
2,048 determinant values, matched the recorded first determinant and
rank on every box, and found exactly one zero in the evaluated
positive control. It took 7.007 s and peaked at 21,626,880 B.
Both runs were ordinary-host diagnostics. The prior direct screen
completed 97 boxes in 14.205 s under its own run conditions; the
current counts give no computational saving for this frozen subset.
The [terminal verifier](verify.py) checks the frozen hashes, all
classifications and counts, audit receipt, and Lean transcript.
`candidate_id` remains `null` because this is a decomposition-stage
predicate.

## Decision and next experiment

The split exposes reusable partial-sum data but the frozen families
reach the same affine-rank boundary while paying to construct minor
vectors. It does not pass a cost-and-rejection gate for N131
promotion. The next exact target-conditioned test should seek a
nonlinear certificate on still-free source-code/root families that
rejects a whole box from fewer operations than enumerating its
assignments, preserving the archived N41 witness. A failure to do
that cheaply should be kept as a source-bound falsifier before any
600-second N131 query.
