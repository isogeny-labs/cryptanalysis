# Exact Q1358 N131 phi pair occupancy

The signed two-leaf sum map for Q1358 phi slots 0 and 1 is injective on its
full `1064 × 1064` state domain. Both the producer and an independent direct
four-sign enumeration found **1,132,096 distinct group sums from 1,132,096
ordered signed pairs**. Thus exact group-point deduplication of this pair
list saves no entries before a target-dependent search.

## Instance and frozen input

The test uses the audited ten-dimensional Q1358 ONB phi subspace for the
ECC2K-130 field of degree 131. The exact curve ID is
`EC1N131Ckb1heb5f1998f20b`; the subgroup order and basis are pinned through
the [source geometry](../n131_phi_torsion_frobenius_domains_20261005/m15_d10_static/d10_exact_geometry_v1.json)
and [protocol.json](protocol.json). There are 532 valid x lifts in each
position and two curve-point signs per lift. Slot 1 is the first Frobenius
conjugate of slot 0. The source geometry records 139,384 distinct usable
subgroup points before orbit folding and 532 folded columns.

The producer [run.py](run.py) builds every valid point, checks the curve
equation, and enumerates two signs on slot 0 with one sign on slot 1. It
negates each computed sum to account exactly for the remaining two sign
choices. [PairSigns.lean](PairSigns.lean) proves that simultaneous sign
reversal negates the sum for any additive commutative group. The independent
[audit.py](audit.py) reconstructs each position separately and directly
enumerates all four sign choices. Both use exact group operations; neither
uses a target or a sampled pair subset.

| Run | Combinations covered | Group additions | Distinct sums | Collision excess | Wall inside script | Peak RSS |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Producer | 1,132,096 | 566,048 | 1,132,096 | 0 | 62.754 s | 102,121,472 B |
| Independent audit | 1,132,096 | 1,132,096 | 1,132,096 | 0 | 119.739 s | 178,618,368 B |

Each run used the checked repository Sage launcher with a frozen accepted
runtime receipt, one worker, and a 600-second/4-GiB envelope. The script
interval begins after Sage startup and includes domain construction and the
full enumeration. These are algorithmic diagnostics on the local host;
`candidate_id` stays null. [verify.py](verify.py) checks the source, input,
result, audit, and Lean receipts.

## Consequence and next gate

The measurement removes exact pair-point deduplication as a compression
mechanism for this Q1358 slot pair. It does not measure a target-conditioned
compatibility predicate on the remaining leaves. Under an explicitly
**heuristic** independent-uniform-sum model, the remaining 13 signed leaves
give `1064^13/r ≈ 3.291` expected completions per fixed pair, or about
96.3% residual coverage. After fixing three leaves, the remaining 12 give
`1064^12/r ≈ 0.00309` expected completions, or about 0.309% coverage.
These are predictions, not observed domain coverage; dependencies among the
phi slots could change them.

The next gate is therefore a target-conditioned **three-leaf** prefix test on
the frozen public point: select a declared ordinary sample and planted
controls, then measure whether a sound two-ended partial-chain constraint
rejects prefixes before a full solver search. Every rejection needs a proof
that the constraint preserves all completions; accepted witnesses need exact
curve replay. Charge target-dependent setup and failed solver attempts.
Promote a filter to the ordinary N131 query only when that gate demonstrates
useful pruning within the one-worker, 600-second, 4-GiB envelope.
