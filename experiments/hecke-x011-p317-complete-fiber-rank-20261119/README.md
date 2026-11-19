# The complete p317 X0(11) trace-2 fiber has full direct-relation rank

Restoring the omitted modular point `(16,60)` gives **40 distinct points**
in the `p=317, |t|=2` fiber. Exhaustive signed group-law relations of support
at most three yield **144 verified rows**, including **22 rows that use the
new point**. Their matrix has rank **39 over F61** and **40 over Q**. The
archived 18 base rows, five class-closed Hecke rows and 80 short-cancellation
rows retain rank **38 over F61** and **39 over Q** when embedded with a zero
40th column. Thus the direct rows supply the new column's missing rank
direction in both fields.

| Relation rows on 40 columns | Rows | Rank over F61 | Rank over Q |
| --- | ---: | ---: | ---: |
| Archived base | 18 | 18 | 18 |
| Base and class-closed Hecke | 23 | 23 | 23 |
| All archived Hecke/cancellation rows | 103 | 38 | 39 |
| All direct signed support ≤3 rows | 144 | 39 | 40 |
| Archived rows and direct rows | 247 | 39 | 40 |

The new point has order five in `E11a1(F317)`, so its cofactor-five
projection has coordinate zero in the frozen order-61 basis. The nonzero
40-coordinate projection vector annihilates every direct row and bounds
their F61 rank by 39. A checked 39×39 inverse modulo 61 gives the matching
lower bound. A checked 40×40 inverse modulo 2 gives an odd nonzero integer
minor and therefore rank 40 over Q. The [Lean certificates](formal/CompleteRankP317.lean)
and [proof map](formal/PROOF_MAP.md) record the finite checks and their
structural implications.

## Frozen inputs and replay

The [protocol](protocol.json) fixes the corrected ledger hash, archived
receipt hashes, point order, row families, coefficient order, rank fields
and resource cap. The [extracted input](archived-inputs.json) retains the
original 39 coordinates, 103 archived rows, projection basis and source
digests. [pre-run.json](pre-run.json) pins its hash before enumeration. The
complete [direct-row ledger](direct-rows.jsonl.gz) retains the 144 verified
relations, including the 22 involving column 39; [result.json](result.json)
retains counts, ranks and ledger hashes.

The pure-Python [producer](run.py) checks that the archived 39 points plus
`(16,60)` equal the complete corrected fiber, verifies every archived and
new row by the curve group law, and computes ranks over Q and F61. The
independent [checked-Sage audit](audit_sage.py) rebuilds `E11a1(F317)`,
checks the new point's order, re-enumerates every signed support-one/two/three
candidate, and recomputes all ranks with Sage matrices. It passed with the
repository [runtime receipt](runtime-info.json); [audit.json](audit.json)
records the result hash and exact rank table.

From this worktree, after the archived input extraction has been checked in:

```sh
python3 experiments/hecke-x011-p317-complete-fiber-rank-20261119/run.py
/Volumes/SSD990/cryptanalysis/sage --runtime-info > experiments/hecke-x011-p317-complete-fiber-rank-20261119/runtime-info.json
/Volumes/SSD990/cryptanalysis/sage -python experiments/hecke-x011-p317-complete-fiber-rank-20261119/audit_sage.py
python3 experiments/hecke-x011-p317-complete-fiber-rank-20261119/formal/generate.py
cd experiments/hecke-x011-p317-complete-fiber-rank-20261119/formal
lake build CompleteRankP317
```

This is an exact relation-rank result for the corrected finite fiber.
Direct-triple enumeration is a generic group-law control; its row yield and
rank here do not measure a single-target IC online interval. The next
discriminating test is to regenerate Hecke-neighbor equations from the
previously omitted point and determine their incremental rank and cost
under the same 40-column identity.
