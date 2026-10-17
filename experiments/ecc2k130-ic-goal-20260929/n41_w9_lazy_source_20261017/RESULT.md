# Exact W9 source eligibility and target-conditioned five-pair lookup

The N41 fixed-seed W9 source admits exactly 71 of its 256 pair codes. An
independent Sage census agrees with the inverse/trace circuit gate on every
code. A five-pair Boolean circuit with the exact 71-code table takes 15.9% less
wall time than the five-gate circuit at a fixed 100,000-conflict diagnostic cap on this
host (17.03 versus 20.24 seconds). The three-gate deferred variant takes
18.03 seconds at the same cap. Both public-point 180-second SAT attempts have
recorded `BOUNDED_UNKNOWN` status and zero learned source cuts because the
solver returned no model within the cap.

The target-conditioned 2+1+2 lookup stores exact two-pair sums, then queries
`target - right_pair - middle` against that table. A checked Sage control
replays the archived five-pair witness with 36 stored entries and 94 streamed
queries on a frozen eight-state-per-slot subset. The full native W9 source
builds 79,424 entries on each two-pair side and found the archived public
relation at orientation 3 after 83,612,805 streamed probes across the orbit.
Independent Sage replay verifies its ten distinct folded columns, exact
five-pair sum, inverse Frobenius transport, and subgroup point.

## Instance and circuit

The field is `GF(2^41)` in polynomial basis with modulus
`u^41 + u^3 + 1`; the curve is `y^2 + xy = x^3 + 1` with curve ID
`EC1N41Ckb1h7d5e80d3c4d0`. The seed mask is 56 (the reciprocal seed
element is 112), source width is 9, and pair rotations are
`0, 6, 12, 18, 24`. The fixed source has 71 usable pair edges, 284 signed
states per slot, 259 usable endpoint masks, and 251 folded endpoint columns.
The original raw public point is `(2026560328086, 1928332930914)`; the
subgroup point is `(1654986373106, 1310318707590) = 4 × raw`. The circuit
tests Frobenius orientation 3 of this point, whose raw coordinates are
`(2105655159232, 891719206310)`.

For the reciprocal pair output `z` and endpoint product `p`, each circuit
slot imposes `(1 + H)z² + pz + H = 0`. The four S3 links use the balanced
three-plus-two tree. `exact5` imposes inverse and trace source eligibility
on all five slots. `exact3` imposes those gates on slots 0–2 and checks
slots 3–4 after a model, learning a precise code exclusion for an invalid
slot. `table5` imposes the exhaustive valid-code table on all five slots.
Folded-column conflicts are checked exactly after a model; each rejected
pair of codes gets a two-slot exclusion clause. The circuit control binds
the archived relation only for assignment verification. Both capped SAT
queries take the public point as input without source masks or signed-pair
assumptions.

| Variant | AND gates | Variables | Clauses | XOR rows | XCNF bytes | 100,000-conflict wall | Public query cap and status |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| `exact5` | 15,047 | 18,340 | 45,733 | 2,720 | 914,024 | 20.24 s, `INDETERMINATE` | fixed-conflict diagnostic only |
| `exact3` | 14,391 | 17,328 | 43,679 | 2,446 | 857,977 | 18.03 s, `INDETERMINATE` | 180.075 s, `BOUNDED_UNKNOWN`, 257,425,408 B sampled combined RSS |
| `table5` | 13,407 | 15,810 | 41,523 | 2,035 | 810,433 | 17.03 s, `INDETERMINATE` | 180.047 s, `BOUNDED_UNKNOWN`, 243,318,784 B sampled combined RSS |

Each fixed-conflict probe used CryptoMiniSat 5 with one thread, the same
oriented public point and source, a 100,000-conflict limit, and a 60-second
wall cap. It was run once per variant in the listed order on an ordinary
shared macOS host. The two 180-second attempts used one thread, a 4 GiB
combined RSS cap, and charged all solver restarts. Their `TIME_CAP` rows,
raw solver output, XCNFs, exact commands, source digests, and measured
intervals are in `exact3_result.json`, `table5_result.json`, and
`probe_result.json`. These intervals are solver-stage diagnostics; the
formula construction and target preparation are retained separately in
`screen_result.json`.

## Exact target-conditioned group join

Let `A`, `B` be points in the first two pair slots, `C` in the third, and
`D`, `E` in the last two. The exact equality is

`A + B + C + D + E = Q` if and only if
`A + B = (Q - (D + E)) - C`.

The native implementation stores each eligible `A + B` with its two state
indices and folded columns, and precomputes the eligible `D + E` points.
For each Frobenius orientation, it streams `C` against `Q - (D + E)` and
checks the table hits for ten distinct folded columns and the full group
sum. This stores 79,424 left-pair entries, compared with the earlier
21,868,032 three-pair entries on the same source. `join_sage_control.py`
independently exercises the exact lookup on the eight-state-per-slot
constructed subset and records one verified hit.

The first native attempt was interrupted after a transient launch stall
before its initial `CHECK_PASS` line; its frozen protocol and empty raw
outputs are preserved. `launch_diagnostic.json` records that the frozen
binary, a byte-identical copy, and the new binary subsequently all launched
and exited promptly with the expected usage error. The separately frozen
retry uses the original 1,420-state input and retains its own protocol,
raw output, resource monitor, and Sage group replay.

| Exact N41 public-point join | Stored left entries | Parent wall, including input and table construction | Sampled worker RSS peak | Verified hit |
| --- | ---: | ---: | ---: | --- |
| Earlier reusable three-pair table | 21,868,032 | 22.410 s | 1,286,029,312 B | Orientation 3, independent Sage pass |
| Target-conditioned two-pair table, retry 1 | 79,424 | 529.865 s | 13,336,576 B | Orientation 3, independent Sage pass |

The new table has 275.3 times fewer stored entries and the sampled worker
RSS is 96.4 times lower. It performs 83,612,805 target-conditioned probes
through the hit, versus a single reusable three-pair table built in the
earlier join. The wall figures are stage-level parent clocks on a shared
host; the new run's `host_sample_retry1.json` records load average 99.96,
100% CPU use during the one-second sample, and 35.53 seconds of worker CPU
after several minutes of wall time. This host envelope makes the 23.6-fold
wall-time difference descriptive rather than a calibrated method ratio.
The one-worker native run completed within its frozen 600-second and 4 GiB
caps. Its terminal receipt is `target_join_result_retry1.json`, and the
independent replay is `target_join_audit_result_retry1.json`.

## N131 size gate

The previously checked W29 N131 source sample found 16,677 usable edges
among 65,536 canonical masks. Its simple width projection is 68,308,992
edges, or about 273,235,968 signed pair states per slot; this is a sample
projection, not a full source census. Materializing the two-pair table at
that projected size would require about 74.7 quadrillion entries. Even
under the optimistic independent-list heuristic that five equal lists only
need `L^5 ≥ r`, the N131 subgroup order
`r = 680564733841876926932320129493409985129` gives
`L ≥ 58,421,660`, hence at least 3.41 quadrillion pair entries for this
table design. At 16 bytes per entry this illustrative storage count is
54.6 PB. The next N131 candidate needs an exact family-rejection rule
or an algebraic compressed index that removes the quadratic table while
keeping target-conditioned queries complete.

## Proof map and reproducibility

| Result | Lean declaration or checker | Exact scope |
| --- | --- | --- |
| Invalid source-code exclusion preserves eligible witnesses | `LazySourceCuts.invalid_code_cut` | Any five-slot code function, conditional on a sound allowed-code predicate. No axioms. |
| Shared folded-column exclusion preserves eligible witnesses | `LazySourceCuts.collision_cut` | Any five-slot code function and column-use predicate, conditional on pairwise column disjointness; standard `propext`, `Classical.choice`, and `Quot.sound` foundations. |
| Two-pair target lookup preserves exact five-point sums | `LazySourceCuts.two_one_two_lookup` | Any additive commutative group; no axioms. |
| N41 inverse/trace gate equals the 71-code table | `census.py` and independent `census_sage.py` | Exhaustive all-256-code check in the exact `GF(2^41)` representation. The finite-field instantiation has an independent Sage checker; a corresponding Lean field implementation is still an open formalization bridge. |
| Constructed five-pair relation and target transport | `audit_sage.py control`, then `audit_target_join_retry1_sage.py` for the full native retry | Exact curve, coordinates, ten folded columns, five signed pair sums, inverse Frobenius transport, and cofactor-four subgroup point. |

The toolchain is pinned to `leanprover/lean4:v4.34.1`; the checked command is
`lean LazySourceCuts.lean` in this directory. `lean.stdout` retains every
`#print axioms` result and `lean.stderr` is empty. The runtime receipt for
every local Sage job is `sage_runtime_info.json`; all Sage scripts here were
run through `/Volumes/SSD990/cryptanalysis/sage -python`. `lean4checker`
was unavailable on this host. Inputs, scripts, formulas, solver output, and
query protocols are hash-pinned in the corresponding result JSON files.
