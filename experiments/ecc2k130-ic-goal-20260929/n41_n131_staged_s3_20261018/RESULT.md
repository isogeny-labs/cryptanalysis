# Staged S3 encoding of the first three pair outputs

**Contribution.** Exposing the first-two-pair intermediate reciprocal
and replacing the first-three-pair F4 norm with two S3 links cuts the
frozen N41 circuit from 111,680 to **21,820 AND gates**. An exact
first-slot ordering produces a 24,855-variable, 70,310-constraint
formula. In a frozen one-worker 20,000-conflict comparison, the
combined circuit used **0.887** times the paired reference decisions
and **0.450/0.648** times its wall. The unpinned N41 public query
reached its 600.084-second cap with status `BOUNDED_UNKNOWN`; its last
flushed restart was near 1.98 million conflicts. This is a measured
throughput improvement and an exact N41 encoding, with a separate
N131 exceptional-case bridge still required.

## Exact domain and exceptional-intermediate audit

The N41 field is `GF(2)[u]/(u^41+u³+1)` on
`EC1N41Ckb1h7d5e80d3c4d0`, with public point
`(1936680952394,910597499030)`. Five aligned W9 pair slots have
rotations `(0,0,12,12,24)`, 71 valid canonical codes per slot and four
signed source states per code. Each first-three-pair code and root,
the first-two-pair sum reciprocal, the preceding four-pair reciprocal,
and both final quadratic roots remain free in the solver query. The
first two codes obey the exact `code0 < code1` symmetry orientation.

The [checked-Sage audit](audit_result.json) exhausts **79,424**
disjoint ordered first-two-pair signed-state combinations on N41.
Their sums never equal the identity or have `x=0`, so the reciprocal
intermediate used by the staged circuit covers every represented N41
relation. The same audit examined both pair-root coordinates for all
512 valid codes in the frozen N131 W29 sample: all 1,024 root
coordinates were distinct and no cross-code pair had reciprocal
product one. Those N131 findings apply to that 512-code sample.
The [audit protocol](audit_protocol.json) pins source hashes, the
accepted Sage runtime, a 120-second wall cap and a 4-GiB envelope.
Arithmetic wall was **6.026 s**, with **244,940,800 B** self peak RSS.

For source-pair reciprocals `a,b,c`, intermediate `m`, and three-pair
reciprocal `z`, the circuit imposes source quadratics for `a,b,c`, then
`S3(a,b,m)=0` and `S3(m,c,z)=0`. The preceding fourth-pair quartic,
final pair quadratic, target S3 quadratic, valid-code rules, and
folded-column collision constraints are retained. The
[proof map](PROOF_MAP.md) includes a Lean-checked result that the two
S3 links imply the exact F4 polynomial, including singular leading
coefficients. The N41 chart audit supplies the concrete intermediate
coverage; signed-group replay remains the final correctness check for
any SAT model.

The [builder](build.py) checked one archived satisfying relation and
32 reachable controls that pass the source and S3 links but fail the
preceding fourth-pair condition. The [ordered builder](build_ordered.py)
exhaustively verified its comparator for all 65,536 eight-bit code
pairs and kept the archived positive. Inputs and implementation are
frozen in the [stage](build_protocol.json) and
[ordered](ordered_build_protocol.json) protocols.

| N41 circuit | AND gates | Variables | CNF clauses | Native XOR rows | Total constraints | Bytes | Build wall |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Prior two-quadratic/F4 reference | 111,680 | 128,017 | 336,899 | 16,174 | 353,073 | 11,020,550 | 28.387 s |
| [Staged S3](build_result.json) | 21,820 | 24,825 | 67,483 | 2,678 | 70,161 | 1,387,820 | 1.846 s |
| [Ordered staged S3](ordered_build_result.json) | 21,820 | 24,855 | 67,632 | 2,678 | 70,310 | 1,390,740 | 14.249 s total staged plus comparator/audit |

The ordered build interval includes an exhaustive comparator audit;
its 12.403 s are conservatively charged together with the 1.846 s
staged build in the ordinary-query stage total.

## Frozen solver probes and public query

The first [probe](probe_result.json) used serial
`quadratic/staged/staged/quadratic` arms. At 20,000 conflicts,
the staged circuit used 31,571 decisions versus 31,602 for each
reference but only 0.526/0.588 times paired wall. It missed the
predeclared 80% decision gate. A separate, frozen
[ordered probe](ordered_probe_result.json) used
`quadratic/ordered-staged/ordered-staged/quadratic` arms. Both
ordered arms used 28,036 decisions versus 31,602 for each reference,
giving decision ratio **0.887** and wall ratios **0.450/0.648**.
Both passed that probe's predeclared 90%-decision/75%-wall gate.
All eight arms ended `INDETERMINATE_CONFLICT_CAP` with monitoring
intact. The probes used one CryptoMiniSat 5.14.7 worker, a
180-second parent limit per arm and a 4-GiB RSS envelope on the
same archived public point.

The [public-query protocol](query_protocol.json) pinned the ordered
formula, one worker, a 590-second solver limit, a 600-second parent
cap and a 4-GiB RSS cap. The [receipt](query_result.json) records:

| Charged component | Value |
| --- | ---: |
| Staged plus ordered build/audit | 14.249 s |
| Solver launch, search, parent stop | 600.084 s |
| Charged stage total | **614.332 s** |
| Sampled peak combined RSS | 230,227,968 B |
| RSS samples / monitor errors | 5,623 / 0 |
| Last flushed restart / approximate conflicts | 2,290 / 1,980,000 |
| Status / stop | `BOUNDED_UNKNOWN` / `WALL_CAP` |

The solver stream has no SAT, UNSAT, or INDETERMINATE terminal line.
Its conflict count is bounded search progress, not a relation-yield
measurement. Independent signed-point replay is prepared in
[replay_model_sage.py](replay_model_sage.py) and is invoked only for
a SAT model. [verify.py](verify.py) passes the pinned sources,
exception audit, all 33 controls, both probe records, Lean output,
query streams, and resource receipt. These wall-time comparisons are
exploratory ordinary-host stage measurements. `candidate_id` remains
`null`.

## Next discriminator

Build a scalable N131 W29 staged circuit with explicit handling of
an identity or zero-`x` first-two-pair intermediate, or prove those
cases absent on the full source domain. The N131 construction must
also encode valid source roots and folded-column disjointness without
enumerating `2^28` codes. Freeze a circuit-size and control preflight
before a one-worker, 600-second/4-GiB public-point query. A terminal
relation then needs independent signed-group verification and complete
single-target accounting before any rho comparison.
