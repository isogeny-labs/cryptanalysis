# Two-pair product resultant for a target-conditioned N41 query

A 37-term polynomial in two source products and the target reciprocal is an
exact necessary condition for the two-pair point sum. It has degree at most
four in each source product, degree eight in the target reciprocal, and becomes
a degree-at-most-four Boolean constraint on the 16 W9 source-code bits after
the target is fixed. This removes both pair-output reciprocals and their
inverse witnesses from the query circuit. On eight frozen, source-diverse N41
holdout keys, each of four members has one resultant-zero admissible code pair
and a checked group witness; each of four nonmembers has zero among 4,964
admissible code pairs.

## Algebra and exact scope

Work over `GF(2)[u]/(u^41+u^3+1)` on `y²+xy=x³+1`, curve ID
`EC1N41Ckb1h7d5e80d3c4d0`. Let `p` be the source product of slot 0 and
`q` that of slot 1 after the slot's Frobenius-six rotation. The reciprocal
pair outputs obey

`C z₁² + p z₁ + H = 0`,  `C⁶ z₂² + q z₂ + H⁶ = 0`,

where the superscript 6 here denotes Frobenius iteration, hence the 64th
field power. The target reciprocal `t` obeys the characteristic-two S3
equation

`(z₁z₂t)² + z₁z₂t + (z₁+z₂)² + t² = 0`.

Eliminating `z₂`, then `z₁`, gives `R(p,q,t)`. The checked-Sage derivation
retains every one of its 37 field-coefficient terms in [resultant.json](resultant.json).
For any two source-valid pairs whose sum is the target, `R=0`. Because this
condition is necessary, any resultant-zero code must still be checked against
the source law and group sum. The exhaustive code census performs that check
for the frozen N41 set; the positive codes each have exactly one witness.

## Frozen experiment

The input set has 71 distinct admissible source codes in each slot, four
signed states per code, and 77 code pairs with overlapping folded columns.
The census therefore evaluates `71²−77=4,964` admissible code pairs per key.
H0–H3 are distinct constructed member targets with source-state witnesses
`(0,13)`, `(71,77)`, `(142,144)`, `(213,205)`; H4–H7 are frozen nonmember
probes. Their point coordinates and input law are retained in the
[holdout keys](../n41_joint_norm_gcd_20261019/diverse_keys.json).

| Key | Resultant-zero codes | Independently checked witness | SAT query status | Solver wall s |
| --- | ---: | --- | --- | ---: |
| H0 | 1 | `(0,13)` | SAT, model replay passed | 1.346 |
| H1 | 1 | `(71,77)` | SAT, model replay passed | 1.829 |
| H2 | 1 | `(142,144)` | SAT, model replay passed | 2.265 |
| H3 | 1 | `(213,205)` | SAT, model replay passed | 3.308 |
| H4 | 0 | — | terminal `UNSAT_UNCERTIFIED` on retry | 1.476 |
| H5 | 0 | — | terminal `UNSAT_UNCERTIFIED` on retry | 1.563 |
| H6 | 0 | — | terminal `UNSAT_UNCERTIFIED` on retry | 1.339 |
| H7 | 0 | — | terminal `UNSAT_UNCERTIFIED` on retry | 1.586 |

Each formula has 16 source-code input variables, 2,457 AND gates, 7,859 CNF
clauses, and 890–893 native XOR rows. The first four SAT assignments satisfy
every formula row and independently replay to the stated curve-point sums.
The four terminal UNSAT lines have no solver proof certificates; the separate
exhaustive census establishes zero resultant-zero admissible codes for these
specific frozen keys. One CryptoMiniSat 5.14.7 worker was allowed 55 seconds,
with a 60-second parent cap and 4-GiB combined-RSS cap. These are ordinary-host
query-stage diagnostics; formula construction, setup, and independent replay
are recorded separately rather than folded into solver wall time.

The first H0–H7 query attempt stopped at H5 stdout creation because the
temporary disk returned `ENOSPC`. Its H0–H3 solver rows and H4 unterminated
row are preserved in [the failure receipt](holdout_first_attempt_failure.json).
The frozen H4–H7 retry produced the terminal rows above. A later Sage-import
`ENOSPC` before the holdout code census executed is preserved separately in
[its failure receipt](holdout_verify_first_attempt_failure.json); the same
checked repository launcher completed the census on retry. Neither first
attempt is silently treated as a mathematical result.

The [archive auditor](audit.py) validates ten frozen protocols, 84
source hashes, all formula and solver-output hashes, retained failures,
model replay, exact code counts, and the Lean axiom output. The audit result
is [audit_result.json](audit_result.json). Protocols frozen under
`/private/tmp/n41_two_pair_product_resultant_20261019` are mapped
content-for-content into this directory for durable replay; their original
bytes and result hashes remain unchanged. `candidate_id` stays null because
this is a query method component, with no complete IC candidate manifest,
relation matrix, or one-target DLP timing comparison.

## Next experiment

Integrate the two-pair resultant as a target-conditioned predicate at a
five-pair addition-tree node. Freeze the ordinary N41 public-point input and
one-worker limits before comparing its full relation-search work with the
existing 20.629-second native three-plus-two relation. First measure whether
the predicate rejects partial-source families before their individual states
are enumerated; then carry the same algebraic node into the frozen N131 W29
five-pair circuit and run its 600-second, 4-GiB public-point gate. Charge
formula construction, all failed models, source checks, and solver search in
that comparison. A reduction in a two-pair membership query alone does not
predict the five-pair search cost.
