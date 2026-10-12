# Ten free W18 pairs increase source density on the frozen N131 point

**A ten-pair target-conditioned N131 circuit passed a full 20-column
constructed assignment and entered ordinary search on the frozen public
point.** Its source extends the nine free W18 pair slots with a tenth free
slot at Frobenius rotation 8, while retaining all four raw preimages and 131
Frobenius target choices in one binary selector. The ordinary solver
reported `s INDETERMINATE` after **588.515 seconds** of target-dependent
work under one worker and 4 GiB. The exact formula and terminal receipt have
been independently replayed.

The instance is `EC1N131Ckb1heb5f1998f20b`, field
`GF(2)[t]/(t^131+t^13+t²+t+1)`, curve `y²+xy=x³+1`, subgroup order
`680564733841876926932320129493409985129`, cofactor four, workload
`cc09e7eb202a`, and frozen public point
`Q=(1052727368764798954359115163823647684025,
2071227447786120917960296877345506689833)`. The ten rotations are
`(0,16,32,48,64,80,96,112,128,8)`. Every slot has 33,191 admissible
canonical seed-212 pair codes; the formula enforces all 20 folded columns
distinct. The full signed-Frobenius factor-base closure has 34,339,816
usable points before folding and 131,068 folded columns under the prior
geometry audit. This is a decomposition-stage experiment with
`candidate_id: null`.

The [N41 pre-promotion control](../n41_w8_tenpair_density_control_20261012/RESULT.md)
found an independently verified, unpinned ten-pair relation on its frozen
public point and raised the rank of its six-, nine-, and ten-pair rows to
three. The N131 [constructed fixture](control_fixture.json) adds one
source pair with new folded columns to the independently checked nine-pair
fixture. Checked Sage [replayed](sage_fixture_result.json) the tenth pair,
raw group sum, 20 distinct columns, and cofactor-four projection. The
[constructed circuit receipt](control_result.json) checked every CNF clause
and native-XOR row. The [frozen protocol](protocol.json) binds those controls,
source hashes, solver binary and flags, public target, one worker, 600-second
target-dependent cap, and 4-GiB combined RSS cap before the control and
ordinary query.

| Exact formula measure | Nine pairs | Ten pairs | Change |
| --- | ---: | ---: | ---: |
| Variables | 231,351 | 258,801 | +27,450 |
| AND gates | 154,245 | 172,560 | +18,315 |
| CNF clauses | 472,203 | 528,856 | +56,653 |
| Native-XOR rows | 72,481 | 81,074 | +8,593 |
| XCNF bytes | 14,253,637 | 16,141,734 | +1,888,097 |

The ten-pair labeled uniform raw-point mean *upper ceiling* in the frozen
source census is about `3.2355×10^14`, multiplying the nine-pair ceiling by
at most 131,307 signed pair states for the added slot. It is a counting
bound, not measured ordinary fixed-point yield. The constructed assignment
proves source/circuit satisfiability on its own constructed point; the
ordinary row below is the measurement on the frozen public point.

| Exclusive ordinary target-dependent phase | Wall |
| --- | ---: |
| Target orbit and fibers | 0.086915 s |
| Formula construction | 3.683780 s |
| XCNF serialization | 0.014658 s |
| Solver search and terminal stop | 584.728336 s |
| Terminal parse | 0.001384 s |
| **Total attempt** | **588.515074 s** |
| Sampled peak parent-plus-solver RSS | **607,961,088 B** |
| Solver terminal line | `s INDETERMINATE` |
| Actual `c rst` rows | **4,901** |

The [query receipt](query_result.json) preserves the exclusive phase sum,
solver exit code zero, no runner-forced stop, all logs, and the exact
`BOUNDED_UNKNOWN` classification. The solver printed 3,202
`TODO disable matrix, performing badly` diagnostics, identifying native-XOR
matrix handling as a concrete next solver-stage target. The
[independent audit](audit_result.json) rebuilt the ordinary XCNF byte for
byte, checked source and phase receipts, and counted the actual restart
rows. Both formula files are stored as deterministic gzip with raw-byte
hashes checked in the [archive receipt](archive_receipt.json); the
[verifier](verify.py) passes after archive replay. Local CPU timing is
exploratory without host-level isolation.

The next experiment should hold this exact formula and target fixed while
changing only CryptoMiniSat's Gaussian-matrix policy, first checking the
solver flag on the satisfiable constructed formula and then using the same
one-worker 600-second/4-GiB public-point gate. Preserve the ordinary
terminal status and complete phase accounting. A further increase in pair
count is not justified by this source-density run alone. The
[proof map](PROOF_MAP.md) records the checked generic target transport
proof and the concrete circuit/curve bridge still open in Lean.
