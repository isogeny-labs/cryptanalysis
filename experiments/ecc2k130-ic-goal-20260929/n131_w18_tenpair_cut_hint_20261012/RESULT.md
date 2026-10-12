# Partial internal cuts preserve the N131 ten-pair witness but remain bounded

Five exact internal-sum hint patterns, each added to the ten true source
selectors and ten true pair outputs of the constructed N131 ten-pair witness,
left CryptoMiniSat in active search at separate **60-second caps**. The
patterns included either target-adjacent internal sum, both target-adjacent
sums, two middle sums, and all four bottom sums. The same parent circuit
completed in **15.612 seconds** when all eight internal sums were supplied
in the preceding frozen control. This measures where the current reciprocal
S3 encoding propagates under progressively supplied true data; it does not
give an ordinary public-point relation.

The curve is `EC1N131Ckb1heb5f1998f20b` over
`GF(2)[t]/(t^131+t^13+t²+t+1)`, with `y²+xy=x³+1`, subgroup order
`680564733841876926932320129493409985129`, and cofactor four. The parent
[constructed control](../n131_w18_tenpair_binary_frob_20261012/RESULT.md)
has ten W18 seed-212 signed pair slots, 33,191 admissible codes per slot,
20 distinct folded columns, and an independently checked Sage group replay.
The circuit's intermediate nodes follow the [frozen tree](protocol.json):
bottom indices 0–3 sum leaf pairs, middle indices 4–5 sum bottom pairs,
index 6 sums the first eight leaves, and index 7 adds leaf eight before
the target link adds leaf nine. This is a decomposition-stage control with
`candidate_id: null`.

The [runner](cut.py) rebuilt the archived parent formula byte for byte and
appended unit clauses for true coordinates only. All arms fixed the same ten
source selectors, ten pair outputs, and constructed target-choice bits.
The [protocol](protocol.json) froze source and solver hashes, hint patterns,
one worker, 60-second parent cap per arm, and 4-GiB combined RSS cap before
execution. The solver clock begins at child launch; fixture reconstruction
and formula preparation are outside that interval.

| Additional exact internal sums | Total appended unit clauses | Solver wall | Peak combined RSS | Restart rows | Status |
| --- | ---: | ---: | ---: | ---: | --- |
| Index 7 | 1,621 | 60.019 s | 563,544,064 B | 545 | `BOUNDED_UNKNOWN` |
| Index 6 | 1,621 | 60.041 s | 486,195,200 B | 1,202 | `BOUNDED_UNKNOWN` |
| Indices 6, 7 | 1,752 | 60.019 s | 371,572,736 B | 1,641 | `BOUNDED_UNKNOWN` |
| Indices 4, 5 | 1,752 | 60.040 s | 300,728,320 B | 498 | `BOUNDED_UNKNOWN` |
| Indices 0–3 | 2,014 | 60.012 s | 286,195,712 B | 463 | `BOUNDED_UNKNOWN` |
| Indices 0–7, prior control | 2,538 | 15.612 s | 238,682,112 B | 497 | `SAT`, independently checked |

The [receipt](result.json) preserves exact solver intervals, parent stops,
exit codes, RSS samples, XCNF archive hashes, log hashes, and restart counts.
Each new arm ended by parent wall cap with exit code `-9` and no SAT or UNSAT
terminal line. The [verifier](cut.py) rebuilt all five archived formulas and
reported `PASS_N131_TENPAIR_CUT_HINT_PROFILE 5`. The prior SAT model was
checked against all CNF and native-XOR rows by its separate
[model audit](../n131_w18_tenpair_leaf_hint_20261012/model_audit_result.json).
Local timing is exploratory without host isolation; terminal outcomes are
bounded by the stated caps.

The next focused test is to fix the **nine S3 branch bits** on this same
constructed assignment while leaving the eight internal coordinates free.
Those bits encode a finite 512-pattern choice, so this diagnostic can
distinguish branch selection from arithmetic propagation. If that succeeds,
an N41 unpinned public-point experiment should test a target-conditioned
branch-pruning rule and count whole-family rejection before any N131
ordinary-query promotion. A full N131 projection remains subject to one
worker, 600 seconds, and 4 GiB. This profile introduces no new
mathematical theorem; the parent proof map retains the formalization
boundary.
