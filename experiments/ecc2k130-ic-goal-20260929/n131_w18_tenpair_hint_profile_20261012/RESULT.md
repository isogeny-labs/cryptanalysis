# Exact partial-sum hints expose the N131 ten-pair leaf inversion barrier

On the constructed N131 ten-pair control, supplying the solver with the exact
reciprocals of **four disjoint bottom sums** still left the formula in active
search at the 90-second cap. The same held when zero, one, or two such sums
were supplied. These are four bounded diagnostics of the existing XCNF
encoding. They identify source-pair inversion beneath the partial sums as a
remaining bottleneck for an output-first target-conditioned method.

The curve is `EC1N131Ckb1heb5f1998f20b`, with
`GF(2)[t]/(t^131+t^13+t²+t+1)`, `y²+xy=x³+1`, subgroup order
`680564733841876926932320129493409985129`, and cofactor four. The source
is the frozen ten-pair W18 seed-212 circuit with 33,191 admissible codes per
pair slot, 20 distinct folded columns, and 524 raw-fiber/Frobenius target
choices. The point in this profile is the [constructed control point](../n131_w18_tenpair_binary_frob_20261012/control_fixture.json),
whose ten-pair assignment passed every original CNF and XOR row. The
previously frozen ordinary public point remains a separate workload. This
is a decomposition-stage diagnostic (`candidate_id: null`).

For each arm, the [runner](profile.py) regenerated the archived control
formula byte for byte, independently reconstructed the known signed point
chain using the prior fixture's group arithmetic, and added unit clauses for
the 131 bits of each selected bottom sum. The four nodes are disjoint pair
blocks `(0,1)`, `(2,3)`, `(4,5)`, and `(6,7)` in the ten-pair tree. The
[protocol](protocol.json) froze the source, formula, solver, hint law, caps,
and code before execution. Each arm used one solver thread, a 90-second
parent wall cap, and a 4-GiB combined RSS cap. Formula loading and hint
derivation were outside the reported solver interval.

| Exact bottom sums supplied | Added unit clauses | Solver wall | Peak combined RSS | Restart rows | Terminal status |
| ---: | ---: | ---: | ---: | ---: | --- |
| 0 | 0 | 90.051 s | 432,930,816 B | 570 | `BOUNDED_UNKNOWN`, parent wall cap |
| 1 | 131 | 90.062 s | 499,040,256 B | 667 | `BOUNDED_UNKNOWN`, parent wall cap |
| 2 | 262 | 90.169 s | 360,349,696 B | 423 | `BOUNDED_UNKNOWN`, parent wall cap |
| 4 | 524 | 90.011 s | 312,999,936 B | 333 | `BOUNDED_UNKNOWN`, parent wall cap |

The [result](result.json) retains exact nanosecond intervals, exit codes,
sampled RSS, formula hashes, log hashes, and actual restart counts. Every
solver process was stopped by the parent at its cap (`exit_code=-9`), with no
SAT or UNSAT terminal line. All four archived XCNF variants replay against
the exact parent bytes, and the [verifier](profile.py) prints
`PASS_N131_TENPAIR_CONSTRUCTED_HINT_PROFILE 4`. Solver timing is exploratory
on an unisolated local host; the decisive observation is that no arm
completed under its frozen cap.

Each fixed bottom sum still leaves the two underlying signed pair codes to
recover from a domain of at most `33,191² = 1,101,642,481` labeled pairs
before the distinct-column shield. The output reciprocals alone do not
provide those masks. The next method should therefore pair a target-derived
partial-sum constraint with a fast exact **inverse index or decomposition
oracle for its source pair block**, and measure the combined target-dependent
work. A next diagnostic can pin the actual pair selectors separately to
distinguish leaf inversion from the remaining upper-tree SAT search; it
should preserve this constructed control and then test an unpinned N41
public-point relation before another ordinary N131 promotion.

This result introduces no new mathematical theorem. The exact point-group
and circuit bridges for the parent constructed assignment are recorded in
its [proof map](../n131_w18_tenpair_binary_frob_20261012/PROOF_MAP.md).
