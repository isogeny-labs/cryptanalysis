# Four fixed seed families admit a fast exact N41 target join

An exact group join exhausts four prescribed N41 diagonal-pair seed families
against the frozen public target in **0.107–0.111 seconds of local process
time**. It finds the checked eight-column relation in the positive tuple and
zero group hits in two witness-independent negative tuples. The corresponding
output-first native-XOR SAT circuits keep all four pair outputs free, but all
three queries reach a 40-second CryptoMiniSat limit with `BOUNDED_UNKNOWN`.
Fixing the positive tuple's three checked S3 root bits also reaches that
limit. Thus the fixed-family output search is cheap as an exact group join,
while these Boolean encodings spend their cap inside the coordinate search.

## Frozen instance and method

The source is the checked diagonal pair table on
`EC1N41Ckb1h7d5e80d3c4d0`, `GF(2)[t]/(t^41+t³+1)`,
`y²+xy=x³+1`, subgroup order `549756390943`, cofactor four, and rotations
`(0,7,14,21)`. The public point is
`(920359962848,755404565011)`. The positive seed tuple
`(7,85,94,171)` is obtained from the earlier checked relation; the two
negative tuples `(220,31,59,64)` and `(145,190,233,221)` are fixed by
SHA-256 of the public reciprocal, source digest, tuple number and slot.
Each family contains every source state whose two masks XOR to its prescribed
seed. This is a point-decomposition component with `candidate_id: null`.

For each tuple, the Boolean producer maps source-state x coordinates to the
complete distinct reciprocal set, encodes one exact BDD per slot, then joins
the four free reciprocals to the public reciprocal with three forward S3
links. The positive complete assignment passes every emitted CNF clause and
native XOR row. The direct join instead enumerates the two pair-state
cross products, hashes the left group sums, computes the required left sum
from the right sum and target, and checks all eight folded columns and the
full group equation on a hit. Its loops exhaust the selected families.

| Selected seed tuple | Signed states by slot | Left/right attempted pairs | Exact group hits | Group join internal wall | SAT variables / CNF / XOR | SAT outcome / solver wall |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| Positive `(7,85,94,171)` | `112,104,128,128` | `11,648 / 16,384` | **1** | **0.107135 s** | `106,555 / 180,897 / 46,187` | `BOUNDED_UNKNOWN / 43.300 s` parent wall |
| Negative `(220,31,59,64)` | `132,116,124,120` | `15,312 / 14,880` | 0 | 0.110473 s | `106,904 / 181,506 / 46,333` | `BOUNDED_UNKNOWN / 44.055 s` parent wall |
| Negative `(145,190,233,221)` | `108,132,112,148` | `14,256 / 16,576` | 0 | 0.106819 s | `107,025 / 181,797 / 46,357` | `BOUNDED_UNKNOWN / 42.940 s` parent wall |

The extra positive chart-root control has three unit clauses on the positive
family formula and reaches `BOUNDED_UNKNOWN` in **40.912 s** parent wall.
Every SAT run used one worker, a 40-second solver limit, a 45-second parent
limit and a 4-GiB RSS ceiling. The sampled solver RSS range was
**115,834,880–218,988,544 bytes**. The positive constructed assignment
check covers **180,897 CNF clauses and 46,187 XOR rows**. These timings are
algorithmic diagnostics on an unisolated local host.

## Verification and interpretation

The positive direct-join state IDs are
`(17678,155,6169,16990)`, exactly the four IDs in the earlier
[independent checked-Sage audit](../n131_w18_allseed_fourpair_20261012/n41_diagonal/audit_result.json).
That audit rebuilds the signed diagonal points, verifies eight distinct
folded columns, the raw group sum, the cofactor projection to the public
point, and novelty of the relation row. The [verifier](verify.py) checks
source and formula hashes, output/receipt hashes, selected family counts,
attempt counts, terminal statuses and the prior Sage witness IDs. The exact
join uses all source states in each selected family and independently checks
its found group equation. The negative results apply to those two fixed
seed tuples and this raw target.

The [main protocol](protocol.json), [join protocol](join_protocol.json) and
[branch protocol](branch_protocol.json) were frozen before their respective
queries. The first query launch ended before solver execution because an
import name resolved to the wrong `build` module; its original frozen
[protocol](protocol_failed_v1.json) is retained, and the corrected producer
was frozen again before measurement. The complete panel verifier reports
`PASS_FROZEN_FOUR_FAMILY_PANEL`.

Supplying four seeds makes this N41 join small. At N131 W18, a literal
fixed-seed family can contain roughly `2^18` signed pair states, so just one
two-family cross product can approach `2^36` candidate pairs before target
matching; selecting among the four seeds also remains unresolved. These
counts explain why the fixed-family join is a diagnostic rather than an N131
query algorithm. The next exact construction should derive compatible seed
families from the public point in bulk, then use the target-conditioned group
join only on the survivors. Its first test is an unpinned N41 relation with
all four seeds chosen by the algorithm, followed by a source-bound N131
work and memory estimate before an ordinary N131 query.

This experiment introduces no new mathematical theorem. The curve and S3
structural proof maps remain in the [source experiment](../n131_w18_allseed_fourpair_20261012/PROOF_MAP.md)
and [forward-root experiment](../n41_allseed_fourpair_forward_20261012/PROOF_MAP.md).
