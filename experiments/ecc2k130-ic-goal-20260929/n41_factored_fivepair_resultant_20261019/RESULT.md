# Factored resultant in the N41 five-pair public-point circuit

The 37-term two-pair resultant admits a compact five-coefficient quartic
factorization. A checked Lean theorem proves that two pair-source quadratics
and their S3 join force the resulting denominator-free constraint over every
characteristic-two field, including degenerate S3 leading-coefficient cases.
The corrected checked-Sage identity reproduces every coefficient of the
frozen N41 polynomial. This supplies an exact, reusable algebraic node for a
target-conditioned five-pair circuit.

Two such nodes were inserted into the frozen W9 five-pair tree on the ordinary
N41 public point at Frobenius orientation 3. The full 71-code source tables,
all ten pairwise folded-column conflict tables, the fifth pair quadratic,
and the two remaining S3 links were imposed. The archived public-point
relation `(0,130,233,283,152)` satisfies all 68,369 CNF clauses and 3,285
native XOR rows in the constructed control. The frozen 180-second solver query
then reached the 185-second parent cap with status `BOUNDED_UNKNOWN`; its
worker RSS remained below 4 GiB in all 874 samples.

## Factorization and proof

Let the two pair-output reciprocals be `z₁,z₂`, their source products be
`p,q`, and the partial-sum reciprocal be `t`. Their exact source equations
are `C z₁²+p z₁+H=0` and `D z₂²+q z₂+J=0`. The S3 equation is
`(z₁z₂t)²+z₁z₂t+(z₁+z₂)²+t²=0`. Eliminating `z₂` gives a quartic in `z₁`
with coefficients

```
U0 = J + D t²                 U2 = D + J t²
K0 = U0² + q²t²              K1 = qt U0
K2 = q²(1+t⁴) + DJt²        K3 = qt U2
K4 = U2² + q²t².
```

For `C ≠ 0`, put `α=p/C`, `β=H/C`,
`L=K1+K2α+K3(α²+β)+K4α³`, and
`M=K0+K2β+K3αβ+K4(α²β+β²)`. The two-stage resultant is

`C³(C M²+p L M+H L²)`.

The initial identity attempt omitted the `C³` factor and failed its exact
polynomial assertion. Its source, protocol, and [failure receipt](factor_first_attempt_failure.json)
are retained. The separately frozen [retry](factor_retry_result.json) passed
the exact 37-term polynomial identity with degrees `(4,4,8)`. Since `C` is a
nonzero fixed source constant, the circuit imposes the equivalent zero test
`C M²+p L M+H L²=0`. The [Lean module](FactoredElimination.lean) states the
necessary implication without division: it multiplies through by the
appropriate powers of `C`, so its hypotheses do not silently assume a
nonzero leading coefficient. The [proof map](PROOF_MAP.md) records the exact
Lean and Sage bridges.

## Frozen public-point experiment

The field is `GF(2)[u]/(u^41+u^3+1)` on `y²+xy=x³+1`, curve ID
`EC1N41Ckb1h7d5e80d3c4d0`. The five W9 pair rotations are
`(0,6,12,18,24)`. The raw public target at orientation 3 is
`(2105655159232,891719206310)`. Each slot has 71 source-valid codes, with
four signed states per code; the witness IDs above are used only in the
constructed assignment control. Query construction takes the target point
and the frozen source law as inputs.

| Circuit on the same oriented public point | AND gates | Variables | CNF clauses | XOR rows | 100,000-conflict wall | Full public query |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| Earlier `table5` | 13,407 | 15,810 | 41,523 | 2,035 | 17.03 s, `INDETERMINATE` | 180.047 s, `BOUNDED_UNKNOWN` |
| Two factored resultants | 22,155 | 25,644 | 68,369 | 3,285 | 16.846 s, `INDETERMINATE` | 185.169 s, `BOUNDED_UNKNOWN` at parent cap |

The factored circuit uses 31 sparse field multiplications and 770 explicit
cross-slot column-conflict clauses. Its XCNF is 1,827,146 bytes. The
fixed-conflict run used one CryptoMiniSat 5.14.7 worker, 100,000 conflicts,
and a 60-second solver cap. The full query used one worker, a 180-second
solver cap, a 185-second parent cap, and a 4-GiB RSS limit monitored from the
host. It produced no terminal SAT/UNSAT line; the raw solver output and
`PARENT_WALL_CAP` receipt are retained. The previous `table5` result came
from a separate ordinary-host run, so the 0.18-second fixed-conflict
difference does not rank the circuits. Both full queries remain censored.

The first full-query launch failed before the solver started when macOS
rejected its pre-exec address-space limit hook. The [failure receipt](query_first_attempt_failure.json)
keeps the frozen protocol and empty streams. The separately frozen retry used
direct host RSS sampling; it stopped at the parent wall cap with zero monitor
errors and a 341,540,864-byte sampled peak. The [artifact auditor](audit.py)
checks six protocols, 34 source hashes, the formula, raw streams, both first
attempt failures, the constructed assignment, and all five Lean axiom
reports. Its result is [audit_result.json](audit_result.json).

`candidate_id` remains null: this experiment measures a point-decomposition
query component. The N131 promotion rule requires a stronger unpinned N41
filtering result on the ordinary point. The next test should select a frozen
subset of resultant output bits at each two-pair node, check complete
source/group validity for every returned model, and add exact exclusion cuts
for failed models. That tests whether early target-conditioned pruning can
reduce the 22,155-gate circuit while keeping all true relations available.
Only a measured gain in complete N41 relation-search work should promote
that variant to the one-worker, 600-second, 4-GiB N131 public-point gate.
