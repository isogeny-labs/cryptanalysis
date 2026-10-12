# Nine exact S3 branch bits do not complete the current N131 ten-pair encoding

On the constructed N131 ten-pair control, supplying **all nine true S3 branch
bits together with all ten true source selectors and pair outputs** left the
current reciprocal circuit in active CryptoMiniSat search. It ended
`s INDETERMINATE` after **58.132 seconds** of solver wall under its frozen
55-second solver setting. Three comparison arms—selectors plus all branch
bits without pair-output hints, and selectors plus pair outputs with only
the first four or last five branch bits—ended the same way. These results
show that enumerating branch choices around this exact XCNF would still
face unresolved internal-coordinate propagation. The earlier all-eight
internal-coordinate control completed with an independently checked SAT
model in 15.612 seconds.

The exact instance is `EC1N131Ckb1heb5f1998f20b` over
`GF(2)[t]/(t^131+t^13+t²+t+1)`, curve `y²+xy=x³+1`, prime subgroup order
`680564733841876926932320129493409985129`, and cofactor four. The ten
W18 seed-212 pair slots each have 33,191 admissible codes, and the parent
constructed witness has 20 distinct folded columns. The raw point sum and
public projection are independently checked by the parent
[Sage fixture](../n131_w18_tenpair_binary_frob_20261012/sage_fixture_result.json).
This is a constructed-target point-decomposition diagnostic
(`candidate_id: null`).

The [runner](branch.py) rebuilt the archived parent formula byte for byte,
then appended unit clauses for the exact branch values in the parent
[constructed assignment](../n131_w18_tenpair_binary_frob_20261012/control_result.json).
The [protocol](protocol.json) froze formula/source/solver hashes and arm
order before execution. Each arm used one solver thread, `--maxtime=55`, a
60-second parent wall cap, and a 4-GiB combined RSS cap. The measured
interval starts at solver launch; fixture reconstruction, formula writing,
and log audit are outside it.

| True hints supplied beyond constructed target choice | Added unit clauses | Solver wall | Peak combined RSS | Restart rows | Terminal line |
| --- | ---: | ---: | ---: | ---: | --- |
| Selectors, outputs, all nine branches | 1,499 | 58.132 s | 696,532,992 B | 1,793 | `s INDETERMINATE` |
| Selectors, all nine branches | 189 | 57.689 s | 637,779,968 B | 2,141 | `s INDETERMINATE` |
| Selectors, outputs, first four branches | 1,494 | 57.377 s | 404,717,568 B | 604 | `s INDETERMINATE` |
| Selectors, outputs, last five branches | 1,495 | 56.693 s | 334,757,888 B | 643 | `s INDETERMINATE` |
| Selectors, outputs, eight internal coordinates, prior control | 2,538 | 15.612 s | 238,682,112 B | 497 | `s SATISFIABLE` |

All four new solvers exited normally with code zero after reporting
`s INDETERMINATE`; the parent did not force-stop them. The
[receipt](result.json) preserves nanosecond intervals, exact terminal
lines, RSS samples, restart counts, formula archives, and log hashes. The
[audit](audit_result.json) reconstructed all four formula archives and
reported `PASS_N131_TENPAIR_BRANCH_HINT_PROFILE 4 0`; the final zero is
the number of SAT models in these arms. The prior complete model has a
separate [full CNF/XOR audit](../n131_w18_tenpair_leaf_hint_20261012/model_audit_result.json).
Local wall values are exploratory without host isolation. The bounded
statuses do not establish mathematical failure of any branch pattern.

For fixed input reciprocals `a,b`, the S3 equation in output `c` is the
Artin–Schreier quadratic

`(1+(ab)²)c²+(ab)c+(a+b)²=0`.

Its two valid roots can be represented as a **functional forward map** of
`a,b` and one branch bit on a guarded nonexceptional chart. The next design
test should encode that forward map at each internal link, with exact
exception handling, rather than leave every intermediate reciprocal as an
independent 131-bit search variable. The earlier
[N41 forward-root control](../n41_n131_zero_sum_forward_20261009/RESULT.md)
provides a related source-bound starting point. A new unpinned N41
public-point relation, whole-family rejection counts, and a complete
N131 600-second/4-GiB work projection remain the promotion gates for the
target-conditioned method.

The displayed quadratic is the same S3 identity already proved in the
parent work; this profile adds no new mathematical theorem.
