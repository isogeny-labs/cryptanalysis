# Exact first-code partition of the N41 target-conditioned circuit

## Contribution

The frozen five-pair N41 circuit can be divided into eight disjoint SAT
formulas by fixing the high three bits of its first source code. The
partition represents **all 71 allowed first-slot codes** and preserves
every satisfying assignment of the original public-point formula. The
Lean proof establishes the interval partition; the read-only verifier
reconstructs and hashes every emitted branch formula from the frozen
10,757,041-byte base XCNF.

Under one sequential worker and a shared 600-second stage budget, **all
eight branches reached their 68-second parent wall cap**. The charged
target-dependent circuit build and panel took **548.243314 seconds**;
the result is `BOUNDED_UNKNOWN`. In particular, branch 2 contains the
archived positive-control assignment with first code 93, yet its unpinned
search also capped. Splitting on three code bits alone therefore supplies
no completed relation search under this budget. This is a decomposition
component with `candidate_id: null`.

## Exact instance and method

The curve is `EC1N41Ckb1h7d5e80d3c4d0`,
`y²+xy=x³+1` over `GF(2)[u]/(u^41+u³+1)`, with subgroup order
`549756390943` and cofactor four. The public point is the frozen
orientation-6 point `(1936680952394,910597499030)`. Five aligned W9
pair slots have Frobenius rotations `(0,0,12,12,24)`, 71 canonical codes
per slot, and four signed pair states per code. The [base circuit](../n41_w9_code_linear_tower_20261017/RESULT.md)
couples the first three pair outputs, the fourth pair, and the fifth
pair to that public point using a rootless final-pair resultant.

Each branch adds three unit clauses to the frozen base XCNF on wires
`[6,7,8]`. For first code `c`, branch `k` requires `c / 32 = k`; the
other five code bits and all four other slots remain free. The branch
formula header increases the constraint count from 339,484 to 339,487.
The [protocol](protocol.json) froze the source hashes, prefix order
`0,…,7`, exact solver binary, one thread, 65-second solver limit,
68-second enforced branch wall cap, 596-second parent panel cap, and
4-GiB combined RSS cap before execution. No source code was fixed from
the archived witness to select a branch.

## Measured search and checks

| First-code prefix | Allowed codes | Parent wall, s | Search status |
| ---: | ---: | ---: | --- |
| 0 | 10 | 68.035 | `PREFIX_WALL_CAP` |
| 1 | 9 | 68.072 | `PREFIX_WALL_CAP` |
| 2 | 9 | 68.110 | `PREFIX_WALL_CAP` |
| 3 | 12 | 68.147 | `PREFIX_WALL_CAP` |
| 4 | 3 | 68.049 | `PREFIX_WALL_CAP` |
| 5 | 9 | 68.135 | `PREFIX_WALL_CAP` |
| 6 | 9 | 68.015 | `PREFIX_WALL_CAP` |
| 7 | 10 | 68.081 | `PREFIX_WALL_CAP` |

The panel parent wall was **544.843394 seconds**. The separately timed
target-dependent base build was **3.399919 seconds**; the saved charged
stage wall is **548.243314 seconds**. The producer made two monotonic
clock reads when recording the panel and total fields; their difference
is 1.209 microseconds. Sampled combined RSS peaked at **119,603,200
bytes**, below the frozen 4-GiB cap. The raw solver streams contain no
terminal SAT or UNSAT line for any branch. These ordinary-host times are
stage measurements, without a host isolation receipt or a solved target
online interval.

The [result receipt](result.json) retains each branch formula hash,
command, raw-stream hashes, stop reason, wall, RSS samples, and last
restart line. The [read-only verifier](verify.py) returned
`PASS_EXACT_PREFIX_PANEL_RECEIPTS` in [verification.stdout](verification.stdout):
it checks frozen sources and protocol, all 71 distinct codes, exact
unit-clause formulas, raw streams, branch statuses, accounting, and the
positive-control branch. The [proof map](PROOF_MAP.md) links the exact
partition and assignment-preservation results to three checked Lean
theorems. `lean PrefixPartition.lean` succeeded with Lean 4.34.1;
`#print axioms` reports only standard foundations. The prior rootless
resultant's checked theorem and independent Sage audit establish the
base circuit's algebraic boundary.

## Next experiment

The final-pair resultant is binary-linear in its eight code bits once
the intermediate reciprocal coordinate `w` is fixed. Form its exact
41-by-8 binary map and test a target-derived image-membership filter on
frozen families of `w` values before expanding final-pair codes. Measure
family rejection, false rejection on the known ordinary relation, and
construction plus query cost against the existing native group join on
the same N41 point. Only a verified unpinned relation and a source-bound
N131 projection justify promotion to the frozen N131 public search.
