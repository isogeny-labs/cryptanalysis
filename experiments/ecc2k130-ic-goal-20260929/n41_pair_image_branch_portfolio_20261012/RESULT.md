# Eight root slices preserve the N41 pair-output BDD search boundary

The exact output-first N41 circuit was searched with **all four pair-output
coordinates free** and each of its three S3 root patterns fixed in turn.
All eight patterns entered active CryptoMiniSat search and reached their
20-second parent caps. The complete serial portfolio took **163.485
seconds** under one worker and 4 GiB, with `BOUNDED_UNKNOWN` on every
slice. This isolates the remaining search cost in selecting four mutually
target-compatible pair outputs, after the complete pair-output sets are
already encoded as BDDs.

The frozen instance is `EC1N41Ckb1h7d5e80d3c4d0` over
`GF(2)[t]/(t^41+t³+1)` on `y²+xy=x³+1`, with subgroup order
`549756390943` and cofactor four. The public point is
`(920359962848,755404565011)` and the raw target reciprocal is
`344545435656`. Each of four pair slots has 15,476 distinct reciprocal
outputs from the complete checked diagonal pair table. The source circuit
is the [parent output BDD](../n41_pair_image_bdd_20261012/RESULT.md),
with 1,370,584 variables, 2,462,010 CNF clauses and 549,845 native XOR
rows. `candidate_id` remains null for this PDP stage.

| Portfolio measure | Recorded result |
| --- | ---: |
| Branch order / coverage | `0,1,2,3,4,5,6,7`; 8/8 |
| Pair-output coordinates fixed | 0/4 |
| Per-slice parent cap / global cap | 20 s / 190 s |
| Total wall, including XCNF generation and solver calls | 163.485 s |
| XCNF write intervals summed / solver intervals summed | 3.013 s / 160.155 s |
| Maximum sampled combined RSS | 721,879,040 B |
| Logged solver restarts summed | 1,333 |
| Statuses | 8 × `BOUNDED_UNKNOWN`, all `SLICE_WALL_CAP` |

The [protocol](protocol.json) froze the public formula, exact pair-output
sets, root wire IDs, solver binary and flags, numeric branch order, one
worker and resource caps before execution. The [journal](slices.jsonl)
retains each generated input hash, raw output hashes, wall interval, RSS,
restart count and stop reason. The [receipt audit](audit.json) verifies the
protocol and all eight terminal records. The parent circuit's positive
fully pinned SAT model passed every XCNF row, and its source chart passed
independent Sage group replay. Those checks establish a positive control;
the eight bounded rows retain their own exact search status. CPU wall
times are exploratory on this unisolated host.

The direct N41 four-pair join in the
[all-seed source experiment](../n131_w18_allseed_fourpair_20261012/RESULT.md)
found and independently replayed an ordinary eight-column relation after
96,094 right probes. That exact group-index control resolves the N41
instance when pair states are enumerated. The output BDD and root slicing
do not replace its target-conditioned join: both leave four pair outputs
to be made compatible with the public point inside SAT.

## Next exact experiment

Construct a condition on **two unresolved two-pair sums and the public
target together**, then measure whole-family rejection before the four
pair-output coordinates are expanded. The existing exact W18
pair-coordinate inverse can verify proposed N131 outputs cheaply, but
the missing step is to generate a sufficiently small target-derived family
of those outputs. A new filter must first preserve and independently
replay ordinary N41 rows under an unpinned source law, then project full
query work and memory inside one worker, 600 seconds and 4 GiB before a
frozen N131 public-query run. The previous output-only affine and
quadratic rank censuses rule out those forms as the needed family filter.

This experiment records an empirical algorithm boundary and introduces
no new mathematical theorem. The S3 root proof map remains with the
[forward-root parent](../n41_allseed_fourpair_forward_20261012/PROOF_MAP.md).
