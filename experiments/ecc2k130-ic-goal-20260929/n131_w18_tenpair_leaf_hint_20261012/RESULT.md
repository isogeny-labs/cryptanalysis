# Upper-tree coordinates complete a constructed N131 ten-pair SAT control

The frozen ten-pair N131 circuit became **SAT in 15.612 seconds** when supplied
with the ten exact source selectors, ten exact pair-output coordinates, and
eight exact upper-tree intermediate coordinates of its constructed witness.
Giving it the selectors alone, outputs alone, or selectors together with
outputs left active search at separate 60-second caps. An independent
literal-level checker verified the completed model against all **531,388 CNF
clauses and 81,064 native XOR rows**. This locates a concrete propagation
boundary for designing a joint target-conditioned constraint.

The curve is `EC1N131Ckb1heb5f1998f20b`, over
`GF(2)[t]/(t^131+t^13+t²+t+1)` with `y²+xy=x³+1`, subgroup order
`680564733841876926932320129493409985129`, and cofactor four. The
constructed point, ten pair states, 20 distinct folded columns, raw group
sum, and cofactor-four projection were independently checked by the parent
[Sage fixture receipt](../n131_w18_tenpair_binary_frob_20261012/sage_fixture_result.json).
The source uses 33,191 admissible seed-212 pair codes per slot and 524
raw-fiber/Frobenius target choices. This profile uses the constructed control
point, with target selector bits fixed to its known choice; it is a
decomposition-stage diagnostic (`candidate_id: null`).

The [runner](leaf.py) regenerated the archived parent XCNF byte for byte,
then appended only unit clauses for true fixture values. Its
[protocol](protocol.json) froze the exact source hashes, four arms, solver
binary and flags, one worker, a 60-second parent cap per arm, and a 4-GiB
combined RSS cap before execution. The solver interval starts at child
launch; fixture loading, circuit reconstruction, formula serialization, and
the later model audit are outside it.

| True information supplied beyond 10 target-choice bits | Added unit clauses including target | Solver wall | Peak combined RSS | Restart rows | Status |
| --- | ---: | ---: | ---: | ---: | --- |
| Ten pair outputs | 1,320 | 60.033 s | 509,984,768 B | 359 | `BOUNDED_UNKNOWN`, wall cap |
| Ten source selectors | 180 | 60.008 s | 340,262,912 B | 1,342 | `BOUNDED_UNKNOWN`, wall cap |
| Selectors and pair outputs | 1,490 | 60.018 s | 422,821,888 B | 461 | `BOUNDED_UNKNOWN`, wall cap |
| Selectors, pair outputs, eight upper-tree outputs | 2,538 | **15.612 s** | 238,682,112 B | 497 | `SAT` |

The [run receipt](result.json) retains nanosecond intervals, exit codes,
sampled combined RSS, archive hashes, complete solver logs, and restart
counts. The first three processes were stopped by the parent (`exit_code=-9`)
without SAT or UNSAT terminal lines. The fourth exited normally with
`s SATISFIABLE`. The [profile verifier](leaf.py) reconstructs all four
archived formulas and reports `PASS_N131_TENPAIR_LEAF_HINT_PROFILE 4`.
The separately frozen [model audit](model_audit_result.json) parses every
solver assignment bit and every archived CNF/XOR row independently of the
circuit evaluator; it reports
`PASS_INDEPENDENT_FULL_XCNF_MODEL_CHECK 258789 531388 81064`.
Local wall differences are exploratory on an unisolated host; terminal
outcomes are exact under the declared caps.

## Design consequence

The previous [bottom-sum hint profile](../n131_w18_tenpair_hint_profile_20261012/RESULT.md)
also reached its 90-second cap with four exact disjoint bottom sums. The new
arms show that fixing the source selectors and all pair outputs still does
not finish this encoding within 60 seconds, whereas supplying the upper-tree
point sums as well does. Therefore an output-first inverse for one pair or
one bottom sum is insufficient as a stand-alone search driver for this
circuit. The next algorithm experiment should derive **joint restrictions on
multiple internal point sums from the public target**, then combine them
with the existing exact W18 pair-coordinate inverse. It must first preserve
all known unpinned N41 public-point relations and measure whole-family
rejection before source masks are expanded. Only a source-bound full-search
projection inside one worker, 600 seconds, and 4 GiB warrants another N131
ordinary-query promotion.

This profile adds no new mathematical theorem. The parent theorem and exact
curve/circuit formalization boundary remain in its
[proof map](../n131_w18_tenpair_binary_frob_20261012/PROOF_MAP.md).
