# Exact target-w and final-code support clauses on N41

## Contribution

The 284-row target-translated final-pair table can be encoded with one
selector per row. An at-least-one clause chooses a translated signed
state; 49 binary implications per selector fix both its 41-bit
intermediate reciprocal coordinate `w` and eight-bit final source
code. This is an exact finite-table constraint on the frozen N41
public target, and the original resultant and folded-column clauses
remain in the full formula. The checked Lean theorem proves the
selector semantics for arbitrary finite tables; the 284 concrete rows
match the independently audited quartic-root table.

The encoding adds **284 variables and 13,917 clauses**, versus 9,362
variables and 28,086 clauses for the prior `w`-only BDD. It also cuts
target-dependent auxiliary construction from **45.932691 s** to
**15.803423 s**. The unpinned one-worker public query reached its
555-second parent wall cap with status `BOUNDED_UNKNOWN`; charged base
build, support build, and search totaled **574.239047 s**. The
component retains `candidate_id: null`.

## Exact instance and construction

The curve is `EC1N41Ckb1h7d5e80d3c4d0`,
`y²+xy=x³+1` over `GF(2)[u]/(u^41+u³+1)`, with subgroup order
`549756390943` and cofactor four. The public point is
`(1936680952394,910597499030)`. Five aligned W9 pair slots have
Frobenius rotations `(0,0,12,12,24)`, 71 canonical codes each, and
four signed states per code. All five codes and their root choices are
free in the public query.

The [build protocol](build_protocol.json) hashes the source, base
circuit and the [284-row table](../n41_w9_target_w_bdd_20261017/RESULT.md)
whose equality to all 71 quartic root sets was independently checked
with Sage. The builder rederives every `w=1/x(Q−E)` and exact final
code, checks equality to that audited table, then emits the selector
implications. The at-least-one clause and 49 implications per row are
equivalent to table membership; the [proof map](PROOF_MAP.md) states the
Lean result and the concrete CNF check. The archived ordinary relation
passes the added clauses for its translated final state.

| Circuit measure | Base | Prior `w` BDD | `w` and code support |
| --- | ---: | ---: | ---: |
| Added variables | 0 | 9,362 | **284** |
| Added CNF clauses | 0 | 28,086 | **13,917** |
| Total variables | 123,218 | 132,580 | 123,502 |
| Serialized XCNF bytes | 10,757,041 | 11,286,287 | **10,953,415** |

The [build receipt](build_result.json) records the formula and table
hashes, **15.803423 s** wall, and 74,465,280 bytes self peak RSS. Its
exclusive phases are source/table 3.317435 s, support and all-row
positive controls 12.299873 s, and serialization 0.186115 s. The
table hash exactly matches the prior checked-Sage table hash.

## Bounded public query

The [query protocol](query_protocol.json) froze the same point and
source, exact solver binary, one thread, a 550-second solver limit,
555-second parent wall cap, and 4-GiB combined-RSS cap. The query ran
through the repository's checked Sage Python after its
[runtime receipt](sage_runtime_info.json) was saved. No source code or
signed state was fixed from the positive control.

| Measured query component | Target-w BDD | Target-w/code support |
| --- | ---: | ---: |
| Prior target-dependent base build | 3.399919 s | 3.399919 s |
| Target-dependent auxiliary build | 45.932691 s | **15.803423 s** |
| Solver launch, search and stop | 530.088494 s | 555.035704 s |
| Charged stage total | 579.421104 s | **574.239047 s** |
| Sampled peak combined RSS | 133,398,528 B | **108,052,480 B** |
| Search status | `BOUNDED_UNKNOWN` | `BOUNDED_UNKNOWN` |

The [query receipt](query_result.json) retains raw solver hashes,
terminal indicators, exact timing, resource samples and the enforced
stop. Its stream contains no terminal SAT or UNSAT status. The
read-only [verifier](verify.py) returned
`PASS_EXACT_TARGET_W_CODE_SUPPORT_RECEIPTS` in
[verification.stdout](verification.stdout). These are ordinary-host
stage diagnostics; a lower build cost and a capped search do not
select a faster relation method.

## N131 source projection and next gate

The explicit-table representation grows with the number of signed
final-pair states. The frozen [W18 source protocol](../n131_w18_two_terminal_fourfiber_20261017/protocol.json)
records **33,191 codes per free pair**, while the
[W20 source protocol](../n131_w20_output_inverse_linear_20261012/protocol.json)
records **132,045**. If each code expands to four signed states as in
this N41 source, a direct 131-bit coordinate-plus-code support table
would emit **19,516,308** and **78,698,820** binary
implications respectively, using only the minimum code bit widths
16 and 18 and before any deduplication. These are conditional size
projections, not measured N131 formulas. They show why this explicit
encoding cannot be promoted solely from its small N41 build.

The next method must represent the sparse target-conditioned image
algebraically while causing rejection before a full four- or six-pair
partial sum is enumerated. Freeze a source-bound N131 construction
estimate, then require an unpinned, independently replayed N41
relation under a complete budget before a public N131 search.
