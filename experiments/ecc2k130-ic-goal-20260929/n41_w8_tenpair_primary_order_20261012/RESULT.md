# Exact primary-wire ordering control for the N41 public ten-pair formula

## Contribution

An exact wire permutation moved all nine S3 branch variables, 1,400 source-state selectors, and four target-fiber selectors ahead of the arithmetic auxiliaries in the frozen N41 ten-pair XCNF. A constructed public-point relation satisfied **all 604,526 CNF clauses and 127,245 native-XOR rows** after renaming. Lean proves that any bijective wire renaming preserves satisfiability of this CNF/XOR semantics. An unpinned, one-worker public query then reached its **180.123-second wall cap** with `BOUNDED_UNKNOWN`, 99 logged restarts, and 171,556,864 B sampled peak combined RSS. This closes simple primary-wire renumbering as a promotion path for this formula and target.

## Frozen instance and method

The curve is `EC1N41Ckb1h7d5e80d3c4d0` over `GF(2)[t]/(t^41+t^3+1)`, with `y²+xy=x³+1`, prime subgroup order `549756390943`, cofactor four, and frozen public point `(920359962848,755404565011)`. Ten free signed W8 pair slots draw 140 states each from rotations `(0,7,14,21,28,35,0,7,14,21)`, with ten distinct source edges. The four raw preimages of the public point are retained. The upstream [functional formula](../n41_w8_tenpair_functional_20261012/RESULT.md) has 289,065 variables; this experiment changes only their names and keeps every clause, XOR row, and target choice. It remains a component study with `candidate_id: null`.

The [producer](experiment.py) reconstructs the source formula and its selector/branch wire lists, then writes a bijection from old wire IDs to new IDs. The first nine IDs are the S3 branch choices; the next 1,400 are source selectors; the next four select a target fiber; all other wires retain their relative order. The [build receipt](build_result.json) records the old and new branch IDs, formula digests, exact row counts, and complete positive-assignment check. A separate [row verifier](verify_permutation.py) checked the mapping of every literal in all 731,771 archived rows; its [receipt](permutation_audit_result.json) passed. The [protocol](protocol.json) froze the source formula, generated XCNF, solver binary, code, resource cap, and public point before the unpinned query. The [query receipt](query_result.json), [raw stdout](solver.stdout), [raw stderr](solver.stderr), and [log audit](audit_result.json) preserve the censored search status. The log audit checked protocol and log hashes, terminal absence, restart count, and cap compliance.

| Frozen N41 public query | Outcome | One-worker parent wall | Peak sampled RSS | Restarts |
| --- | --- | ---: | ---: | ---: |
| Original functional XCNF, same source and public point | `BOUNDED_UNKNOWN` | 180.025 s | 296,337,408 B | 601 |
| Primary-wire ordered XCNF | `BOUNDED_UNKNOWN` | 180.123 s | 171,556,864 B | 99 |

The parent killed the ordered solver at its 180-second cap (`exit=-9`); no `SAT` or `UNSAT` terminal was printed. The original run used the same solver flags and 4-GiB cap. These local timing and restart figures are exploratory because host isolation was not established. Restart counts describe different solver trajectories and are not a work-normalized speedup measure. The exact formula equivalence and positive-assignment verification do not depend on CPU timing.

## N131 transfer gate

The corresponding all-seed W18 N131 source has exactly 34,482,792,912 signed pair states **per slot** in the frozen [source census](../n131_w18_bucketed_public_20261012/projection_result.json). Literal independent one-hot encoding of ten such slots requires 344,827,929,120 selector bits. Even at one bit per variable and no clause or solver overhead, that is **43,103,491,140 bytes**, 10.036 times the 4-GiB RSS cap. The [projection producer](project.py) and [receipt](projection_result.json) compute this integer bound; `VariableOrder.n131_onehot_memory_gate` checks the arithmetic in Lean. This bound applies to the literal selector representation in this experiment. The existing compact Boolean W18 source representation has a different memory model and remains the appropriate substrate for any new joint filter.

## Next method gate

The earlier [joint pair-output relaxation](../n41_two_pair_partial_joint_linear_20261011/RESULT.md) rejected N131 controls while two 32-bit output suffixes were unresolved, but explicit prefixes at that width already identify source leaves. The next test should put the joint S3 constraint directly on compact W18 source-mask variables and retain at least two unresolved pair outputs. It should report whole-family rejection before leaf selection on a frozen unpinned N41 public query, then an exact N131 construction and memory bound. A fresh N131 600-second relation query is warranted only after that source-bound gate passes.
