# Plus-only adjacent leaf on the frozen N131 public point

**Restricting the adjacent pair to the same signed source point removed
6,079 AND gates, 10,289 variables, 18,237 CNF clauses, and 4,209
native-XOR rows from the constructed ten-pair circuit.** A complete
assignment and independent Sage point reconstruction passed. The
one-worker query on the frozen N131 public point ran for 600.030608
seconds of target-dependent work and stopped at its declared cap with
status `BOUNDED_UNKNOWN`.

For source point (P), Frobenius τ, (a=1/x(P)), and first-join
reciprocal (w), this variant enforces only

\[
  w(1+a^2)=a,\qquad w=1/x(P+τ P).
\]

The [source gate](gate_result.json) binds the prior independently
replayed N41 public relation: the repeated edge at rotations 0 and 1
used matching signed source pairs, and its folded row raised prior
rank 3 to 4. The frozen N131 root table has **66,382 distinct plus
outputs**, compared with 132,764 outputs when both signs are allowed.
The [proof map](PROOF_MAP.md) links the checked adjacent algebra to
this exact source restriction and states the remaining formal bridge.

## Frozen control and public query

The curve is `EC1N131Ckb1heb5f1998f20b` over
`GF(2)[t]/(t^131+t^13+t^2+t+1)`. The public point is
`(1052727368764798954359115163823647684025,
2071227447786120917960296877345506689833)`, workload
`cc09e7eb202a`. Ten pair slots use nine independent W18 source edges;
slots 0 and 1 reuse one edge at adjacent rotations. The
[protocol](protocol.json) fixes all source hashes, target selector,
one worker, 600-second target-dependent cap, 4-GiB sampled
combined-RSS cap, and solver flags before control and query. The
[checked Sage runtime](sage_runtime_info.json) was saved beforehand.

| Frozen constructed control | Plus-only | Both signs |
| --- | ---: | ---: |
| Variables | **240,899** | 251,188 |
| AND gates | **160,066** | 166,145 |
| CNF clauses | **489,798** | 508,035 |
| Native-XOR rows | **76,077** | 80,286 |
| Full assignment check | all rows pass | all rows pass |

The [constructed assignment](control_result.json) passed every clause
and XOR row. The independent [Sage control](control_sage_audit.json)
rebuilds the ten signed pair points, checks the plus-only first join,
sums the constructed raw target, and verifies its cofactor-four
subgroup transport. The ordinary public formula has 240,878
variables, 160,062 AND gates, 489,786 CNF clauses, and 76,060
native-XOR rows. Formula savings compare exact stages on the same
source and target policy; they do not establish a solver-time ordering.

| Exclusive public-query phase | Seconds |
| --- | ---: |
| Four raw fibers and target orbit | 0.093742 |
| Formula construction | 3.267720 |
| XCNF serialization | 0.012736 |
| Solver launch, search, and stop | 596.655964 |
| Terminal parse | 0.000446 |
| **Target-dependent total** | **600.030608** |

The solver logged 5,042 restart rows. The parent stopped it at the
600-second sampled deadline, including 31 ms of monitoring overshoot;
sampled combined peak RSS was 671,596,544 B. Exit `-9` had no
terminal SAT/UNSAT status and no model. The exact transcript and phase
costs are in the [query receipt](query_result.json). `BOUNDED_UNKNOWN`
is a censored outcome for this resource cap. The
[independent audit](audit_result.json) checks source binding, formula
counts and hashes, status, time phases and memory cap. The
[compressed XCNF archives](archive_result.json) replay byte for byte,
and the [read-only terminal verifier](verify.py) checks the complete
record from those archives. This is an ordinary-host decomposition
stage; `candidate_id` remains `null` while the full IC pipeline is
unresolved.

## Next target-conditioned experiment

The plus-only leaf is smaller, while both same-point SAT attempts
reached the cap. The next test should put the public target into a
constraint on **two still-free partial-sum families before their full
combination is expanded**. Use the verified N41 plus-only relation as
a witness-preservation control, freeze a source-code family and exact
target-conditioned rejection predicate, and measure how many entire
families it excludes per unit work. Promote to N131 only if an exact
source-bound realization survives that gate, then charge the ordinary
public query and independently replay any returned relation. The
rank, factor-log, unseen-target descent, and matched-rho stages remain
in the active single-target objective.
