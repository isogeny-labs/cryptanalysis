# Source-first ordering retains the N41 public search boundary

**An exact variable permutation moved the four target-fiber flags and 1,400 signed source selectors ahead of every arithmetic auxiliary in the functional-slope N41 ten-pair formula.** All 378,056 XCNF rows were independently matched literal for literal to the frozen source under the bijection, and the known relation still satisfied every row. The unpinned search on the same public point reached its 180-second parent cap with no SAT or UNSAT terminal line. Thus simple target/source decision order does not close this formula under the declared limit; the next change must constrain source-state families with information from the public point.

## Frozen exact method

The source is the [functional full-point circuit](../n41_fullpoint_functional_slope_20261012/RESULT.md) for `EC1N41Ckb1h7d5e80d3c4d0`, over `GF(2)[t]/(t^41+t³+1)`, on `y²+xy=x³+1`. It has ten free signed W8 pair-state slots, 140 states each, a ten-distinct-edge shield, and all four raw preimages of the frozen public point `(920359962848,755404565011)`. The method retains every clause, XOR row, source state, and target choice. It only renames the 121,456 Boolean variables so that flags become IDs 1–4 and the source selectors become IDs 5–1,404. This is a solver-order component with `candidate_id: null`.

The [build protocol](build_protocol.json) froze the runner and source identities before construction. The [build receipt](build.json) records the source and reordered hashes, counts, exact positive-assignment check, and phase times. The [query protocol](query_protocol.json) then froze the ordered formula and one-worker solver command before the public search. The [independent auditor](verify.py) rebuilt the permutation, checked every transformed literal in all 325,702 CNF and 52,354 native-XOR rows, verified the positive control IDs against the prior checked model, and audited raw solver logs and caps. Its [receipt](audit.json) passed. The generic satisfiability-preserving variable-renaming proof is linked in the [proof map](PROOF_MAP.md).

| Same N41 public point and one-worker 180-second cap | Original functional slope | Target/source ordered |
| --- | ---: | ---: |
| Variables / CNF / native-XOR | 121,456 / 325,702 / 52,354 | Identical |
| XCNF bytes | 7,034,401 | 6,966,231 |
| Solver terminal status | `PARENT_TIME_CAP` | `PARENT_TIME_CAP` |
| Parent solver wall, exploratory | 180.028 s | 180.058 s |
| Restart rows | 252 | 413 |
| Sampled combined RSS | 126,746,624 B | 115,736,576 B |

The shorter serialized file reflects shorter variable-number strings after renaming; it is the same Boolean formula. Restart counts reflect different solver trajectories and do not establish a controlled speedup. The [query receipt](query.json), raw stdout/stderr, archived XCNF, and protocol preserve the terminal absence and parent kill. CPU timings are exploratory on an unisolated host. The prior pinned control supplies the checked positive assignment; this experiment measured the unpinned public query.

## Next gate

The exact XCNF renaming leaves the public search active, as did the earlier reciprocal-only primary-order variant. Further syntax-only ordering is a weak route to the N131 relation objective. The next experiment should insert an **exact public-target condition on multiple unresolved source-pair families**, count rejected families before state expansion, and find an unpinned N41 row with independent group and folded-column replay. Its complete source-bound N131 work and memory projection must fit one worker, 600 seconds, and 4 GiB before the frozen N131 public point is queried. The subsequent IC steps remain rank, factor logs, unseen target descent, scalar replay, and matched same-point rho timing.
