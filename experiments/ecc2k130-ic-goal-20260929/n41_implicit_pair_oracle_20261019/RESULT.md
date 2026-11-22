# N41 target-conditioned implicit second-pair oracle

An algebraic product-span test decided eight frozen target-conditioned
pair-sum keys in agreement with an exact 79,424-entry group-law census. It
scanned the 284 first-slot states per key, **without a quadratic left-pair
sum table or a second-slot point table during lookup**. Four known-member
keys each produced one exact reconstructed second-pair witness; four
nonmember keys from the public target's first join probes produced no
product-span hit. The eight checked-Sage query intervals totaled 2.549
seconds. The formula `p=Cz+H/z` and its whole-family rejection implication
are proved in pinned Lean 4.

## Input law and method

The curve is `EC1N41Ckb1h7d5e80d3c4d0`, over
`GF(2)[u]/(u^41+u^3+1)` with `y²+xy=x³+1`; its subgroup order is
549,756,390,943 and cofactor four. The W9 fixed-seed source has 71 valid
mask codes and 284 signed pair states per slot. The first two pair slots
have Frobenius rotations 0 and 6. The [frozen keys](keys.json) include the
first two states of the independently replayed
[public-point join hit](../n41_target_conditioned_2p1_join_20261018/audit_result.json),
three further exact members, and four misses obtained from
`target − third-state − right-pair` in the join's first orientation. The
key census counted 79,424 admissible left-pair entries and the same number
of distinct point keys. All source and runtime hashes are frozen before
the queries.

For each key `K` and first-slot point `A`, compute `B=K−A`. Undo the
second-slot Frobenius rotation, set `z=1/x(B)`, and recover the only possible
source product `p=Cz+H/z`. Reduce `p` against the eight-dimensional
product basis. A failed reduction rejects every second-slot source code at
once. On a hit, check the inverse/source trace conditions, reconstruct the
two factor-base leaves for both signs, test the exact group point, and
enforce disjoint folded columns. The [proof map](PROOF_MAP.md) states the
mathematical implication and the finite implementation boundary.

| Arm | Frozen keys | Result | Per-key wall interval |
| --- | --- | --- | ---: |
| Algebraic two-pair XCNF, 3,925 variables / 9,190 clauses / 752 native XOR rows | Four members and four nonmembers | Eight `BOUNDED_UNKNOWN`, each `WALL_CAP`; one worker, 10 s solver / 12 s parent cap, 4 GiB RSS cap | 12.005–12.056 s |
| Finite-code-table ablation, retaining pair-output quadratics and S3 | One member and one nonmember | Two `BOUNDED_UNKNOWN`, each `WALL_CAP` under the same caps | 12.014–12.032 s |
| Direct product-span oracle | Four members and four nonmembers | Eight exact agreements with census; four reconstructed witnesses | 0.211–0.543 s internal checked-Sage time |

The algebraic XCNF member formulas have complete constructed assignments
that satisfy every clause and XOR row. The table ablation substitutes the
exact 71-code finite list for the source validity equations; it also accepts
the constructed member. The bounded SAT rows are retained with raw solver
streams and exact cap reasons. The first query-launch attempt with system
Python failed before starting a solver because `psutil` was missing; its
[failure receipt](query_first_attempt_failure.json) is preserved. The
measured panel ran through the checked repository Sage launcher.

The span basis has rank eight. The direct oracle examined 2,272 first-slot
states across eight keys. For each member, 283 of 284 candidates failed
the span test and the sole survivor passed trace, point, and column checks.
For each nonmember, all 284 candidates failed the span test. These counts
are exact for the frozen keys. The runs are ordinary-host algorithmic
diagnostics, not an isolated CPU speed comparison. `candidate_id` remains
`null` because a complete IC pipeline has not been fixed.

## Decision and next iteration

The span test is an exact, compact second-family rejection rule. It avoids
the quadratic pair table used by the earlier indexed join, while doing 284
first-state group subtractions for each N41 key. Directly scanning the
projected N131 first-state family for every key would not meet the frozen
one-worker, 600-second relation gate. The next step is to solve the span
condition **jointly over first-family code variables** so one operation
rejects many first states, then compare against these same eight keys and
the archived public join hit. The N131 promotion gate remains the ordinary
public-point relation under its frozen resource cap, with independent group
replay; the single-target online and paired rho measurement follows that
gate.

Run `python3 audit.py` to verify the [terminal audit](terminal_audit.json):
six frozen protocols, 43 source hashes, all eight key labels, all ten
bounded SAT receipts, and both Lean theorem reports. Local Sage commands
use `/Volumes/SSD990/cryptanalysis/sage -python`.
