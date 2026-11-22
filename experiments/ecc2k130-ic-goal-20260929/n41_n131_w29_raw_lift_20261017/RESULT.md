# Second trace-compatible raw lift in the W9/W29 five-pair search

The frozen N41 W9 source produces a **second, independently replayed ordinary five-pair relation** for the same subgroup public point. It uses the other trace-compatible raw lift and a distinct set of five signed pair states: Frobenius orientation 1, state IDs `(31,220,216,191,145)`, and ten distinct folded factor-base columns. On the corresponding N131 W29 circuit, the second lift required more fixed-conflict SAT work than the first in its completed probe: **448,338 versus 413,447 decisions** and approximately **68 million versus 45 million propagations** at 100,001 conflicts. This branch did not pass the promotion gate for a 600-second public query.

## Exact input and relation

Both fields use `E: y²+xy=x³+1` and the same frozen source states as the first-lift five-pair experiment. The field polynomials are `u^41+u^3+1` and `u^131+u^13+u²+u+1`. For `T=(0,1)`, the existing [public-lift correction](../rotated_fouratom_public_lift_correction_20261010/RESULT.md) establishes `x(R+T)=1/x(R)` for nonexceptional `R`. The checked-Sage preparation script independently verified `2T=O`, `4R0=4(R0+T)=Q`, and trace-zero reciprocal x for both raw lifts. This is an application of the prior coordinate identity; this experiment introduces no new mathematical theorem.

| Field | Curve ID | Raw lift 0 x | Raw lift 1 x | Public subgroup x |
| --- | --- | ---: | ---: | ---: |
| N41 W9 | `EC1N41Ckb1h7d5e80d3c4d0` | 2026560328086 | 548056158626 | 1654986373106 |
| N131 W29 | `EC1N131Ckb1heb5f1998f20b` | 877610862732227974378969808549299291499 | 770794657550069419943936485965613853151 | 1052727368764798954359115163823647684025 |

The [lift receipt](lift_targets.json) also gives both y coordinates, reciprocal x values, source hashes, and subgroup points. The N41 [protocol](n41_raw1_protocol.json) freezes the second-lift target, the same 1,420 signed source states, native binary and source hashes, one worker, 600-second parent wall cap, and 4-GiB worker RSS cap before the search. The native 3+2 join returned `HIT 1 31 220 216 191 145` after 237.848 parent-wall seconds; sampled peak worker RSS was 1,280,180,224 bytes. The independently checked-Sage [audit](n41_raw1_audit_result.json) reconstructs all ten source points, their pair sums, Frobenius transport, target raw point, ten distinct folded columns, and `4R1=Q`. The first-lift witness had orientation 3 and state IDs `(0,130,233,283,152)`, so these are distinct ordinary relations on the same public subgroup point. This host was heavily shared; the two native wall times are correctness-run observations, not a calibrated search-speed comparison.

## N131 matched solver gate

The [second-lift builder](build_n131_raw1.py) changes the target reciprocal from `1/x(R0)=770794657550069419943936485965613853151` to `1/x(R1)=877610862732227974378969808549299291499` in the same W29 exact-source 3+2 circuit. It preserves the one-row output trace gate. Each formula has 76,859 AND gates; the trace form has 121,205 variables, 232,430 clauses, and 42,503 native XOR rows. The [build receipt](build_n131_raw1_result.json) pins circuit, runtime, and formula hashes. The N131 control for the target-independent circuit and trace rule is in the preceding [trace-parity experiment](../n41_n131_trace_parity_20261017/RESULT.md); the second-lift construction changes only the public target constant.

The [probe protocol](probe_n131_lifts_protocol.json) fixes raw-lift order `0,1,1,0`, one CryptoMiniSat worker, 100,000 requested maximum conflicts, a 150-second parent wall cap per run, and 4-GiB combined RSS cap. It hashes both formulas, solver, build receipts, script, and checked Sage runtime. Raw solver output and the [result receipt](probe_n131_lifts_result.json) retain every run, including the censored repeat.

| Order | Raw lift | Terminal status | Conflicts | Decisions | Reported propagations | Parent wall | Peak combined RSS |
| ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: |
| 0 | 0 | `INDETERMINATE` | 100,001 | 413,447 | 45M | 46.581 s | 105,775,104 B |
| 1 | 1 | `INDETERMINATE` | 100,001 | 448,338 | 68M | 111.991 s | 133,464,064 B |
| 2 | 1 | `WALL_CAP`; no terminal solver status | last flushed restart about 97K | unknown | unknown | 150.107 s | 121,094,144 B |
| 3 | 0 | `INDETERMINATE` | 100,001 | 413,447 | 45M | 57.037 s | 117,506,048 B |

CryptoMiniSat rounds propagation counts to millions in its terminal output. The completed raw-lift-1 run used about 1.51 times the reported propagation and 1.084 times the decisions of raw lift 0 at equal conflicts. The second raw-lift-1 run is censored at its wall cap; its last flushed restart line shows roughly 97K conflicts but cannot be promoted to a 100,001-conflict measurement. Both completed arms ended at a search cap rather than a SAT or UNSAT conclusion. Shared-host wall variation precludes an online-time claim. The N131 point, source, and formula are a point-decomposition stage configuration; `candidate_id` remains `null` until a complete IC pipeline is specified and measured.

## Decision and next experiment

The second lift increases the available ordinary-relation search domain on N41 and gives an independently verified relation there. Its N131 fixed-work probe is less favorable than the first lift, so no second-lift full-cap public query was launched from this gate. The existing [cofactor-class census](../n131_w18_cofactor_class_preflight_20261017/RESULT.md) and [four-class sieve](../n131_w20_fourclass_sieve_20261015/RESULT.md) show that simply exposing the order-four class is weak for related source laws. The next experiment should derive a nonhomomorphic, target-conditioned predicate on two or more unresolved partial-sum families and measure how many source families it rejects before signed-point expansion; N41 ordinary relations and frozen N131 controls remain the correctness gates.

Reproduce the preparation and independent replay through the checked launcher:

```sh
./sage -python experiments/ecc2k130-ic-goal-20260929/n41_n131_w29_raw_lift_20261017/prepare_lifts_sage.py
./sage -python experiments/ecc2k130-ic-goal-20260929/n41_n131_w29_raw_lift_20261017/audit_n41_raw1_sage.py
```

The first preparation uses exclusive-create outputs and is intended for a fresh artifact directory; this receipt preserves the original outputs and SHA-256 bindings. Run the non-Sage builder and probe only after verifying their frozen source and formula hashes. The saved [runtime receipt](sage_runtime_info.json) records the accepted installed Sage build.
