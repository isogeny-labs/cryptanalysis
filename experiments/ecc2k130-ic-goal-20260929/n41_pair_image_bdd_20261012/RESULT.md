# Exact pair-output BDD builds inside 4 GiB; public search reaches its cap

An output-first circuit now represents the **complete N41 diagonal
pair-output reciprocal set** in each of four slots with reduced ordered
decision diagrams. Each slot has 30,952 signed pair states and 15,476
distinct reciprocal outputs; its BDD has between 207,068 and 207,403
nodes. The complete four-slot circuit builds with 828 MB sampled peak RSS,
and its constructed positive assignment satisfies all 2,462,010 CNF
clauses and 549,845 native XOR rows. CryptoMiniSat solved and independently
replayed the fully pinned control. The ordinary public query entered active
search and reached its frozen 190-second wall cap with `BOUNDED_UNKNOWN`.

## Exact source and construction

The instance is `EC1N41Ckb1h7d5e80d3c4d0` over
`GF(2)[t]/(t^41+t³+1)`, curve `y²+xy=x³+1`, subgroup order
`549756390943`, cofactor four. The frozen public point is
`(920359962848,755404565011)`; the formula binds raw preimage reciprocal
`344545435656`. The source is the [checked all-seed diagonal pair table](../n131_w18_allseed_fourpair_20261012/n41_diagonal/pairs.tsv)
with rotations `(0,7,14,21)`. Source pair states were mapped to `1/x`,
deduplicated by coordinate, and represented by an exact BDD in each slot.
Three forward S3 links join the four free pair outputs to the target. This
is a point-decomposition component (`candidate_id: null`).

| Exact stage | Result |
| --- | ---: |
| Signed pair states per slot | 30,952 |
| Distinct reciprocals per slot | 15,476 |
| BDD nodes by slot | 207,238; 207,068; 207,178; 207,403 |
| Complete circuit variables / AND gates | 1,370,584 / 820,572 |
| CNF clauses / native XOR rows | 2,462,010 / 549,845 |
| Public XCNF size | 62,752,873 B |
| Frozen construction wall / sampled peak RSS | 41.416 s / 827,899,904 B |
| Constructed assignment | All CNF and XOR rows passed |

The [source census](census_result.json) and [output values](output_values.json)
bind every reciprocal set to the frozen pair table. The [build
protocol](build_protocol.json) fixed a one-worker, 180-second, 4-GiB
construction envelope before the run. The [build receipt](build_receipt.json)
and [audit](build_audit.json) retain the formula hash, phase intervals,
output hashes and sampled memory. The source pair table's prior checked-Sage
audit verifies its signed points and group law; the current circuit check
verifies membership and three root links for the constructed positive chart.

## Frozen solver outcomes

| Run | Free pair outputs | Free root bits | Parent cap | Wall | Sampled peak RSS | Outcome |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| Positive control | 0 | 0 | 35 s | 1.810 s | 608,468,992 B | SAT; full XCNF model replay passed |
| Ordinary public query | 4 | 3 | 190 s | 190.028 s | 703,643,648 B | `BOUNDED_UNKNOWN`; 936 restarts; wall cap |

The [solver protocol](solver_protocol.json) fixes both exact formulas,
source and solver hashes, flags, one worker, and 4-GiB RSS ceiling. The
[control audit](control_audit.json) parses the returned model and checks
every one of its 2,462,177 CNF clauses and 549,845 native XOR rows. Its
primary coordinates and branches are the previously checked positive group
chart. The [ordinary receipt](ordinary_result.json) and
[audit](ordinary_audit.json) retain active search, terminal absence,
restart count, cap, peak RSS and raw-output hashes. The ordinary result is
an exact bounded diagnostic; the local CPU wall times are exploratory
without host-level isolation.

The BDD describes pair-output *coordinates*. It does not encode each
output's source-state identifier or the eight-distinct-column shield;
any ordinary SAT model would require pair-state lookup and independent
group/column replay before becoming a verified relation. Thus the pinned
SAT control verifies the encoding and positive chart, while the ordinary
row measures its unpinned search boundary.

## Next exact constraint

Test a **branch-first portfolio of the three root choices** on this same
output-first formula, with four pair-output coordinates free and a frozen
total one-worker envelope. The earlier eight-mask circuit became cheap
when all root patterns were sliced, while the present BDD gates expose
the sparse output domains directly. Any SAT model must be replayed through
the pair table, eight-column rule and checked-Sage group sum. If that
portfolio remains bounded, the next design must couple two unresolved
pair-output families through the target before exposing their coordinates
to SAT. The N131 W18 source has 34,482,792,912 signed pair states per
rotation, so a literal output table is a control; a transferable method
needs the existing compact exact W18 pair-output inverse as its membership
oracle.

This experiment adds an empirical circuit and search boundary, not a new
mathematical theorem. The S3 root statement and its formalization status
remain in the [parent proof map](../n41_allseed_fourpair_forward_20261012/PROOF_MAP.md).
