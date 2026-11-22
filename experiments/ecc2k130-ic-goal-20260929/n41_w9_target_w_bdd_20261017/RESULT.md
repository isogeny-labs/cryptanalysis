# The exact target-translated final-pair domain as an N41 BDD

## Contribution

The frozen N41 final-pair source gives **284 distinct target-conditioned
intermediate reciprocal coordinates**. Translating each signed final
pair state `E` by the public point `Q` yields `w=1/x(Q−E)` and its exact
source code. Independent checked Sage found that, for each of the 71
allowed codes, the rootless final-pair resultant is a degree-four
polynomial whose **four field roots are exactly the four translated
table values**. This gives a complete finite domain for `w` on this
source and target.

A reduced BDD for the 284 values adds **9,362 variables and 28,086 CNF
clauses** to the frozen five-pair XCNF while retaining all original
source and resultant constraints. The archived ordinary relation passes
the added gate. The one-worker unpinned public query reached its
530-second parent wall cap with status `BOUNDED_UNKNOWN`; the charged
base build, BDD build, and search totaled **579.421104 seconds**.
The component remains `candidate_id: null`.

## Exact instance and construction

The curve is `EC1N41Ckb1h7d5e80d3c4d0`,
`y²+xy=x³+1` over `GF(2)[u]/(u^41+u³+1)`, with subgroup order
`549756390943` and cofactor four. The public point is
`(1936680952394,910597499030)`. Five aligned W9 pair slots have
Frobenius rotations `(0,0,12,12,24)`, 71 canonical codes each, and
four signed states per code. All five codes and their root choices
remain free in the solver query.

The [build protocol](build_protocol.json) hashes the checked source,
base circuit and builder, fixes natural BDD bit order `0,…,40`, and
sets a 60-second build cap and 4-GiB RSS cap. It translates all 284
signed final states by `Q`; none enters an exceptional identity or
zero-x residual chart, and all 284 `w` values are distinct. The BDD
imposes exact Shannon equations for membership in that set and a true
root. The original target-coupled resultant and folded-column
collision clauses are retained. The [proof map](PROOF_MAP.md) gives the
source and quartic-root argument and the formalization boundary.

| Circuit measure | Frozen base | Target-w BDD |
| --- | ---: | ---: |
| Variables | 123,218 | 132,580 |
| CNF plus native-XOR constraints | 339,484 | 367,570 |
| Extra target-domain CNF clauses | 0 | 28,086 |
| Serialized XCNF bytes | 10,757,041 | 11,286,287 |

The [build receipt](build_result.json) records the exact table and
formula hashes, **45.932691 seconds** of target-dependent build wall,
and 81,739,776 bytes self peak RSS. Its phase times are source/table
2.663625 s, BDD and assignment controls 43.233554 s, and serialization
0.035512 s. The archived positive `w` passes every emitted BDD clause;
two absent coordinates fail the BDD root. The independent
[checked-Sage audit](audit_result.json) recomputed all 284 translations
and completely factored the resultant for all 71 codes: every quartic
has exactly four roots, matching the table. Its arithmetic interval
was **22.479004 s** and self peak RSS 221,102,080 bytes. The accepted
[Sage runtime receipt](sage_runtime_info.json) was saved before that
audit.

## Bounded public query

The [query protocol](query_protocol.json) froze the public formula,
solver binary and flags, one thread, a 525-second requested solver
limit, 530-second parent wall cap, and 4-GiB sampled combined-RSS cap.
The first host-`python3` launch ended before solver startup because
`psutil` was unavailable; its exact transcript is retained as
`query_attempt1.stderr`. The second launch used the repository's
checked Sage Python and the unchanged frozen query script and formula.

| Measured query component | Value |
| --- | ---: |
| Prior target-dependent base build | 3.399919 s |
| Target-dependent BDD build | 45.932691 s |
| Solver launch, search, and parent stop | 530.088494 s |
| Charged stage total | **579.421104 s** |
| Sampled peak combined RSS | 133,398,528 B |
| RSS samples / monitor errors | 5,113 / 0 |
| Last logged restart / approximate conflicts | 969 / 486,000 |
| Query status | `BOUNDED_UNKNOWN`, `WALL_CAP` |

The [query receipt](query_result.json) retains exclusive costs,
command, raw-stream hashes, terminal indicators and stop reason. The
solver stream has no terminal SAT or UNSAT status. The read-only
[verifier](verify.py) checks frozen hashes, table/root audit, circuit
counts, raw streams, accounting and resource bounds; its
[output](verification.stdout) passes. These are ordinary-host stage
measurements without a host isolation receipt or a recovered
single-target scalar.

## Next experiment

The exact table did not make the `w`-only BDD search finish within its
budget. A smaller support encoding uses one selector per translated
state and directly implies both its 41 `w` bits and eight final-code
bits. This removes most BDD auxiliary variables and feeds the final
code into existing folded-column constraints. Compare its frozen
whole-query receipt with this run, then project the encoding's clause
growth from the exact N131 source count before any N131 public query.
