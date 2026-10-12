# Compact seed-sum circuit preserves the four-family search boundary

The exact N41 four-pair source circuit accepts four prescribed pair-seed sums
with **32 native-XOR rows** while leaving all eight source masks, four pair
outputs and both middle coordinates free. It has **14,803 variables**, about
one seventh of the earlier output-BDD family circuits, and its checked
positive assignment satisfies all **35,804 CNF clauses and 2,924 XOR rows**.
On the same frozen target and seed tuples, the positive query and two
exhaustive-miss controls each entered active CryptoMiniSat search and reached
their 45-second parent caps as `BOUNDED_UNKNOWN`.

## Exact source and controlled change

The source is the checked N41 diagonal W8 factor base on
`EC1N41Ckb1h7d5e80d3c4d0` over `GF(2)[t]/(t^41+t³+1)`, with
`y²+xy=x³+1`, subgroup order `549756390943`, cofactor four, rotations
`(0,7,14,21)`, and public point `(920359962848,755404565011)`.
The existing [all-seed circuit](../n131_w18_allseed_fourpair_20261012/RESULT.md)
enforces rational source support, the exact pair reciprocal equation, eight
distinct folded columns, and three target-coupled S3 links. The current
producer adds, for every bit of every slot, the exact equation
`mask_a[bit] XOR mask_b[bit] = seed[bit]`. It changes no other source or
target condition. This is a point-decomposition component with
`candidate_id: null`.

The positive tuple `(7,85,94,171)` comes from the earlier checked relation.
The two witness-independent tuples `(220,31,59,64)` and
`(145,190,233,221)` were fixed in the preceding
[four-family panel](../n41_four_family_joint_20261012/RESULT.md) using a
SHA-256 rule that includes the target reciprocal. The exact group join
exhausted these declared families against the same raw target: one hit for
the positive tuple, zero for each control. Their statuses are labels for
this SAT panel, not assumptions about its solver output.

| Seed tuple | Exact group hits | Formula variables / CNF / XOR | Solver restart rows | Parent wall | Sampled solver RSS peak | SAT status |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| `(7,85,94,171)` | **1** | `14,803 / 35,804 / 2,924` | 973 | 45.036 s | 312,655,872 B | `BOUNDED_UNKNOWN` |
| `(220,31,59,64)` | 0 | `14,803 / 35,804 / 2,924` | 883 | 45.033 s | 301,088,768 B | `BOUNDED_UNKNOWN` |
| `(145,190,233,221)` | 0 | `14,803 / 35,804 / 2,924` | 449 | 45.023 s | 189,792,256 B | `BOUNDED_UNKNOWN` |

Each query used one CryptoMiniSat worker, a requested 40-second solver
limit, a 45-second parent wall cap, and a 4-GiB RSS ceiling. The parent
stopped all three while they were still producing search diagnostics; none
emitted a terminal SAT or UNSAT line. These ordinary-host timings are
exploratory diagnostics. The exact terminal statuses and source-bound work
are the evidence; a capped run does not decide its formula.

## Audit and implication

The [frozen protocol](protocol.json) binds the source, public target, three
seed tuples, solver binary and resource limits before construction. The
[verifier](verify.py) checks every source and formula hash, XCNF row count,
the precise 32 seed-sum XOR rows, positive complete-assignment check, solver
logs and receipt hashes, active restart rows, and the preceding exact group
labels. Its saved output is [here](verify.stdout). The positive hit is the
same four-state relation already independently replayed in checked Sage.

The output-BDD family panel used roughly **106,555–107,025 variables** and
also reached its frozen limits on these three tuples. The current compact
source-mask encoding removes about 86% of those variables but does not
settle even the supplied-family positive control within its cap. Formula
size alone is therefore a weak guide for this exact search stage. Further
work should prioritize a target-conditioned family-elimination or output
generation rule that decides many source families before asking SAT to
search their coordinates. The promotion gate is still an unpinned N41
public relation with the seed families selected by the method, followed by
a source-bound N131 work and memory estimate under one worker, 600 seconds
and 4 GiB.

This experiment adds measured search evidence rather than a new theorem.
The source and S3 mathematical proof maps remain with the
[all-seed circuit](../n131_w18_allseed_fourpair_20261012/PROOF_MAP.md).
