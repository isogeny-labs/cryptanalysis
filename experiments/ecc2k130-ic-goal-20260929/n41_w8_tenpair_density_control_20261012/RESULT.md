# Ten free W8 pairs give a third N41 public-point relation

**An unpinned five-versus-five join found a ten-pair relation on the frozen
N41 public point in 14.862 seconds of one-worker runner wall.** Independent
checked Sage rebuilt all ten pairs from the source masks, verified their raw
sum and cofactor-four public-point projection, and formed a 20-column folded
row. Twelve of its columns lie outside the earlier six- and nine-pair rows,
so these three rows have rank three together.

The exact instance is `EC1N41Ckb1h7d5e80d3c4d0`, field
`GF(2)[t]/(t^41+t^3+1)`, curve `y²+xy=x³+1`, subgroup order
`549756390943`, and cofactor four. The common public point is
`(920359962848,755404565011)`. The accepted relation sums to raw preimage
index one, `(946309826754,403262551014)`, which projects to that point.
All ten signed W8 pair states were free. The source chooses slots
`(0,1,2,3,4,5,0,1,2,3)`, with each slot drawing from its frozen 140-state
list; the hit has ten distinct underlying folded edges. This is a component
control (`candidate_id: null`).

The [protocol](protocol.json) froze the public-point source file, native
source and binary, included group arithmetic, deterministic random seed,
five-million-kept-state cap on each half, four raw fibers, one worker,
180-second total wall cap, and 4-GiB combined RSS cap **before** execution.
The native program checked 128 Sage reference additions before building the
left table. Its [receipt](receipt.json) preserves the exact hit, counts,
phase markers, stdout/stderr hashes, exit code, cap status, and sampled RSS.

| Stage item | Frozen result |
| --- | ---: |
| Left kept states / attempts | 5,000,000 / 6,741,384 |
| Left construction through `LEFT_DONE` | 10.2516 s native elapsed |
| Right kept probes / attempts at hit | 898,812 / 1,211,875 |
| Group point matches before accepted hit | 5 |
| Target-dependent right search to hit | 4.1848 s native elapsed |
| Whole runner wall | 14.861791 s |
| Peak sampled parent-plus-child RSS | 311,984,128 B |
| Raw fiber / source edges / folded columns | 1 / 10 / 20 |
| Novel columns / rank with prior six and nine | 12 / 3 |

The [audit protocol](audit_protocol.json) bound the native receipt and
stdout, checked Sage runtime, geometry, fixture, and independent replay
source before the audit. Checked Sage regenerated each raw W8 point, its
signed pair and Frobenius rotation, then checked the ten-pair group sum,
cofactor-four target, Frobenius quotient coefficients, 20-term folded row,
and independence from the two prior rows. The [audit result](audit_result.json)
reports `PASS_INDEPENDENT_N41_PUBLIC_TENPAIR_RELATION`; the
[receipt verifier](verify.py) passes. This is a same-public-point correctness
and density control. Local timing is exploratory without a host-isolation
receipt.

This control supports testing ten free W18 pair slots on the frozen N131
public point. The N131 promotion must first freeze a source-bound ten-pair
formula with the exact 20-column shield, prove a constructed ten-pair
assignment, retain the one-worker 600-second/4-GiB cap, and independently
replay any ordinary model. The increased relation multiplicity is a design
hypothesis until that ordinary query produces and verifies a row. The
[proof map](PROOF_MAP.md) separates the checked abstract transport theorem
from the remaining concrete formalization bridge.
