# N41 resultant-coordinate projection and dead-gate screen

Projecting each five-pair resultant node onto 24 frozen field coordinates
preserved the archived ordinary N41 public-point relation in a complete
assignment check. The one-worker query reached its 65-second parent cap with
`BOUNDED_UNKNOWN`, no solver model, zero RSS monitor errors, and a
310,132,736-byte sampled peak below the 4-GiB limit. Exact backward slicing
then removed only **5 of 22,155 AND gates**. This measures the cost of the
proposed partial-equation variant before any N131 promotion.

The selected coordinate indices were the first 24 values of
`(17i+5) mod 41`: `[5,22,39,15,32,8,25,1,18,35,11,28,4,21,38,14,31,7,24,0,17,34,10,27]`.
The same fixed indices were used on both two-pair nodes. The rest of the
five-pair topology, 71-code source tables in each slot, 770 cross-slot
column-conflict clauses, fifth pair quadratic, two remaining S3 links,
oriented raw public point `(2105655159232,891719206310)`, and one-worker
resource envelope were frozen. The witness IDs `(0,130,233,283,152)` were
used only in the constructed formula control.

| N41 formulation | Enforced resultant field coordinates per node | AND gates after dead-gate slice | Query outcome |
| --- | ---: | ---: | --- |
| Complete factored nodes | 41 | 22,155 | 185.169 s, `BOUNDED_UNKNOWN` at parent cap |
| Projected nodes | 24 | 22,150 | 65.154 s, `BOUNDED_UNKNOWN` at parent cap |
| [One-coordinate structural screen](../n41_projection1_gate_screen_20261019/RESULT.md) | 1 | 20,791 | No solver query; gate-count screen |

The 24-coordinate formula was built with the same checked Sage launcher and
runtime receipt as the earlier full circuit. The constructed witness satisfies
all 68,335 CNF clauses and 3,285 native XOR rows. The projected solver query
used one CryptoMiniSat 5.14.7 worker, a 60-second solver cap, a 65-second
parent cap, and direct host RSS monitoring against 4 GiB. Its raw stream
contains no terminal SAT/UNSAT line. The [query receipt](query_result.json)
preserves the cap, resource samples, and stream hashes. The query did not
return a candidate code tuple, so there was no model to pass to the planned
complete signed-state group check.

The [structural slicer](slice_xcnf.py) separates definitional AND triples
and native XOR rows from independent constraints, then retains only their
transitive dependencies and renumbers reachable variables. On the frozen
24-coordinate XCNF it retained 22,150/22,155 AND gates and 3,216/3,285
XOR definitions. The one-coordinate screen retained 20,791 AND gates.
Thus removing resultant output equations alone leaves most of this
factorization's nonlinear work reachable. The [artifact auditor](audit.py)
checks three frozen protocols, 19 source hashes, the built and sliced
formula hashes, the witness control, and the capped query record; its
[result](audit_result.json) passes.

The next algebraic variant needs to reduce the number or width of field
multiplications before constraints are emitted. Row projection of this
factorization does not meet the N41 ordinary-relation gate for N131 transfer.
`candidate_id` remains null while the complete IC pipeline and one-target
timing comparison are unresolved.
