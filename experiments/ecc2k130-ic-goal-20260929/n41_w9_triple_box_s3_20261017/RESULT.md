# A target-conditioned S3 index resolves the full N41 three-code completion

With two archived pair states fixed, an exact reciprocal-coordinate index
tested **all 313,158 eligible N41 three-code boxes** against the frozen
public point. It retained exactly two boxes, the archived ordinary relation
and its equal-rotation swap, and rejected every other eligible box before
expanding its 64 signed assignments. A separate group-sum implementation
rebuilt all **37,488** indexed left coordinates and both exact witnesses.
The frozen index construction took **5.709 s** and the public-target join
**0.429 s** on this ordinary host. This is a complete conditional
three-code search with slots 0 and 4 fixed to archived witness states;
the frozen public-point relation search with all five slots free remains
the next algorithmic gate.

## Source, target, and box predicate

The source is `EC1N41Ckb1h7d5e80d3c4d0` over
`GF(2)[u]/(u^41+u³+1)`, `E: y²+xy=x³+1`, with 71 canonical W9 pair
codes and four signed states per code in each of five slots. Their
Frobenius rotations are `(0,0,12,12,24)`. The public raw point is
`(2026560328086,1928332930914)` at orientation 6. The fixed states
are slot 0 ID 105 and slot 4 ID 111, taken from the previously
[independently verified relation](../n41_n131_w29_rotation_alignment_20261017/RESULT.md).
Thus the target-dependent partial point is
`T=Frob^6(Q_raw)-P₀-P₄=(465614337187,923968010151)`.

Let `X_c` be the two distinct nonzero reciprocal x-coordinates of one
code's four signed pair states. For source codes `c₁,c₂`, construct
the exact finite root set

`L(c₁,c₂) = {z: S₃(a,b,z)=0, a∈X_c₁, b∈X_c₂}`.

For code `c₃`, construct the target-conditioned set

`R_T(c₃) = {z: S₃(c,1/x(T),z)=0, c∈X_c₃}`.

An admissible three-code witness must have
`L(c₁,c₂) ∩ R_T(c₃) ≠ ∅`. The [producer](full_index_sage.py) builds
an index from each left reciprocal coordinate to its source-code pair,
then queries it with each right coordinate. It checks ten distinct
folded columns before exact point replay. The nonexceptional chart has
four S3 quadratics and eight left coordinates per eligible code pair,
and two quadratics and four right coordinates per code. The
[Lean proof map](PROOF_MAP.md) checks S3's quadratic form and completeness
of its two roots; the independent group index checks the curve bridge
for every tested code family.

## Frozen N41 results

The [1,025-box panel](panel.json) was frozen from source columns before
evaluating the target: one archived positive box and 1,024 distinct
source-only pseudorandom boxes. Its [producer](result.json) solved
6,150 S3 quadratics and retained only the positive box, with state
triple `(244,66,47)`. The [independent panel audit](audit_result.json)
reconstructed every left coordinate from sixteen signed group sums,
every right coordinate from four target subtractions, and all 65,600
point-assignment comparisons. It found no exceptional charts.

The [full index protocol](full_protocol.json) then froze the whole
`71³` code domain subject to ten distinct folded columns. The
[full producer result](full_result.json) and [independent group
audit](full_audit_result.json) agree:

| Full N41 conditional search | Exact result |
| --- | ---: |
| Eligible slot-1/slot-2 code pairs | 4,686 |
| Indexed left reciprocal-coordinate records | 37,488, all distinct |
| Eligible three-code boxes after column filtering | 313,158 |
| Target-side slot-3 code families | 69 |
| Algebraic survivor boxes | 2: `(61,11,16)` and `(61,16,11)` |
| Exact state witnesses | `(244,47,66)` and `(244,66,47)` |
| Producer chart exceptions / independent group chart exceptions | 0 / 0 |
| Producer left-index construction / target join | 5.709 s / 0.429 s |
| Producer / independent auditor self peak RSS | 274,890,752 B / 233,635,840 B |

The swap is expected because slots 2 and 3 share Frobenius rotation 12.
The group auditor constructed all 16 signed sums for each eligible
left code pair and all four target subtractions per eligible right code,
then reproduced the full coordinate-table digests, candidates, and
exact point identities. Its checked-Sage group-index interval was
31.787 s. The frozen producer used one checked-Sage worker, a
180-second parent timeout, and a 4-GiB observational RSS boundary;
there was no independent process-tree memory monitor. The producer
timings are stage diagnostics on a shared host:
the fixed states were selected retrospectively, and the index
construction is charged separately from its target query. Process
launch and source loading are outside these intervals. Neither run
establishes a full five-slot online IC time.

## Literal W29 transfer boundary

The [audited N131 W29 source sample](../n41_n131_fivepair_w9_w29_20261017/sample_audit_result.json)
contains **16,677 distinct valid canonical codes**. On the degree-131
field, one folded Frobenius column contains at most 131 source leaves;
with the fixed-seed canonical pairing, it is incident to at most 131
codes. Four fixed columns therefore exclude at most 524 first-slot
codes. For each retained first code, its two columns and the four fixed
columns exclude at most 786 second-slot codes. The exact rank-28
source-product decoder gives at most one second code per output
reciprocal coordinate. Across the two first-code roots, the exceptional
equal-root and reciprocal-root tests can exclude at most four further
second codes.

Hence at least

`(16677−4·131)(16677−6·131−4) = 256,622,711`

ordered code-pair families from this already validated subset have a
nonexceptional coordinate to store. A **literal index with one raw
131-bit coordinate per such family** needs at least
`256622711·17 = 4,362,586,087` bytes, **67,618,791 bytes above 4 GiB**,
before code IDs, hash overhead, further roots, or the rest of the IC
worker. The [transfer calculation](transfer_result.json) binds the sample,
its independent audit, the rank certificate, and the N41 full index.
The bound applies to this full-coordinate-per-family representation;
an implicit or compressed family predicate is a different method.
The [independent transfer audit](transfer_audit_result.json) recomputed
the integer bound and checked the same column-incidence argument on the
complete N41 source: its maximum was two codes per column, and the
corresponding conservative bound of 3,465 eligible pair families lay
below the 4,686 actually observed.

## Next experiment

Represent the slot-1/slot-2 family condition implicitly, for example by
reducing the target-conditioned S3 resultant against their two
linearized source-product annihilators, while keeping slot 3 free.
The first gate is a frozen unpinned N41 public-point run in which slots
0 and 4 are selected by the algorithm, with construction, every failed
box, exact group/column replay, and a source-bound work and memory
model charged. The literal coordinate index is not promoted to the
one-worker 600-second/4-GiB N131 public-relation query. This remains a
point-decomposition stage with `candidate_id: null`; relation rank,
factor logs, target descent, and the same-point rho comparison are
later gates of the active goal.

Run `python3 -B verify.py` to reproduce the read-only
[terminal binding check](terminal.json) of inputs, results, proofs, and
N131 arithmetic.
