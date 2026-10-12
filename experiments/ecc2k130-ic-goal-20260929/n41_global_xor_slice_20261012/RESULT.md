# Global source-mask XOR slices retain the N41 public search boundary

Eight or eleven deterministic, independent XOR constraints across all eight
source masks leave the exact N41 public-point circuit compact and its source
families unpinned. The eight-row known-relation control satisfies every
formula row, but reaches a 60-second solver cap. Two witness-independent
ordinary slices, with 8 and 11 rows respectively, both enter active
CryptoMiniSat search and reach their 150-second parent caps as
`BOUNDED_UNKNOWN`. This tests a low-cost global affine slice as a way to
reduce the nonlinear coordinate search; at these caps it does not supply
the required unpinned relation.

## Frozen source and slice law

The curve is `EC1N41Ckb1h7d5e80d3c4d0` over
`GF(2)[t]/(t^41+t³+1)`, with `y²+xy=x³+1`, subgroup order
`549756390943`, cofactor four, and public point
`(920359962848,755404565011)`. The checked diagonal W8 source uses
four pair slots at rotations `(0,7,14,21)`. The [all-seed exact circuit](../n131_w18_allseed_fourpair_20261012/RESULT.md)
already enforces rational source support, pair equations, cross-slot
distinct folded columns and the public-target S3 chain. The current
producer adds 8 or 11 parity rows on the 64 primary source-mask bits.
Each row touches every pair slot; the 11 rows are independent, and the
ordinary 8-row system is a prefix of the ordinary 11-row system.

SHA-256 of the frozen source and public reciprocal selects the parity
coefficients. The ordinary right-hand sides use only that source and
target. A separate control sets its eight right-hand sides from the
previously checked relation, so its full positive assignment is known
before the run. No source masks or pair outputs are pinned in any query.
The [panel](panel.json) and [protocol](protocol.json) froze the equations,
source, solver binary, one worker and 4-GiB RSS ceiling before formula
construction. This is a point-decomposition component with
`candidate_id: null`.

| Query | XOR slice rows | Formula variables / CNF / native XOR | Solver restart rows | Parent wall / cap | Peak solver RSS | Status |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| Known-relation control | 8 | `14,803 / 35,804 / 2,900` | 786 | 60.021 / 60 s | 125,599,744 B | `BOUNDED_UNKNOWN` |
| Ordinary public slice | 8 | `14,803 / 35,804 / 2,900` | 1,652 | 150.026 / 150 s | 251,772,928 B | `BOUNDED_UNKNOWN` |
| Nested ordinary public slice | 11 | `14,803 / 35,804 / 2,903` | 1,959 | 150.037 / 150 s | 327,139,328 B | `BOUNDED_UNKNOWN` |

The solver was requested to stop five seconds before each parent cap; the
parent stopped all three active searches without a terminal SAT or UNSAT
line. Their statuses are bounded observations, not unsatisfiability
decisions. The positive control passes all **35,804 CNF clauses and 2,900
native XOR rows**. The ordinary right-hand sides were fixed without the
known witness, so either ordinary run would have required a complete model
audit, signed-point reconstruction and independent Sage replay before
counting as a relation. The local wall intervals are unisolated solver
diagnostics, not an IC/rho speedup comparison.

The [terminal verifier](verify.py) checks every frozen source and formula
hash, the rank and exact contents of the appended XOR rows, control
assignment, solver logs, restart counts and cap receipts. Its saved output
reports `PASS_GLOBAL_XOR_SLICE_PANEL_AUDIT`.

## Next method gate

The positive control and both witness-independent slices leave the search
undecided. Further source-wide random parity rows would reduce the expected
number of N131 relations while giving no measured N41 solver benefit here.
The next construction should use the public point to eliminate complete
seed/product families through the upper S3 constraints, before Boolean
coordinate search. It must recover an unpinned N41 row with independent
group replay and demonstrate a source-bound N131 query plan inside one
worker, 600 seconds and 4 GiB. The current N131 ordinary relation and
single-target pipeline gates remain open.

This experiment adds a measured algorithm boundary, not a new mathematical
theorem; the underlying curve and source proof map remains with the
[all-seed circuit](../n131_w18_allseed_fourpair_20261012/PROOF_MAP.md).
