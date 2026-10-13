# Adjacent-link S4 target constraint

The reciprocal three-pair addition constraint has a 24-monomial resultant and a six-term elementary-symmetric form. Both forms were checked against Sage's polynomial resultant. On frozen N41 and N131 signed group controls, its four field roots are exactly the four inverse-x coordinates of the eight signed sums. A direct native-XOR circuit removes the free intermediate field element, but doubles the AND gates in the arithmetic core at both field sizes.

## Identity and proof

Write `a,b,c` for reciprocal-x coordinates of three pair sums and `t` for the target reciprocal-x coordinate. For two adjacent reciprocal S3 links with an intermediate `z`, set

```
f(z) = A z² + B z + C,  A = 1+(ab)², B = ab, C = a²+b²
g(z) = D z² + E z + F,  D = 1+(ct)², E = ct, F = c²+t².
```

In characteristic two their quadratic resultant is

```
R = (AF+DC)² + (AE+DB)(BF+EC).
```

Let `U=AF+DC`, `V=AE+DB`, and `W=BF+EC`. The Bézout identity

```
R = (Df+Ag)² + V(Ef+Bg)
```

shows directly that every common root of the two S3 links satisfies `R=0`, including cases where a leading coefficient vanishes. Expanding in `a,b,c,t` gives 24 monomials, with degree at most four in each variable. With elementary symmetric functions `e1=a+b+c+t`, `e3=abc+abt+act+bct`, and `e4=abct`, the same polynomial is

```
R = e3⁴ + e1²e4² + e1⁴ + e3²e4 + e1²e4 + e3².
```

The coefficient identities are kernel-checked in [S4Polynomial.lean](S4Polynomial.lean) and [S4Bezout.lean](S4Bezout.lean). The independent checked-Sage audit compares the actual multivariate polynomial and finite-field roots; see [PROOF_MAP.md](PROOF_MAP.md) for the precise formalization boundary.

## Frozen audit and circuit measurement

The checked launcher was `/Volumes/SSD990/cryptanalysis/sage -python`, with [runtime information](sage_runtime_info.json) saved before the audit. The v3 audit used one process, a 120-second wall cap, a 4 GiB direct-PID sampled RSS cap, and frozen source/input hashes in [audit_protocol.json](audit_protocol.json). It exited successfully in 7.264 seconds, with sampled peak RSS 265,748,480 bytes. This is a correctness audit, not a solver benchmark.

| Field and modulus | Constructed control inputs | S4 roots | Signed group roots | Degree |
| --- | ---: | ---: | ---: | ---: |
| GF(2^41), `T^41+T^3+1` | 3 pair points | 4 | 4, exact set equality | 4 |
| GF(2^131), `T^131+T^13+T^2+T+1` | 3 pair points | 4 | 4, exact set equality | 4 |

The curve in each control is `y²+xy=x³+1`; the exact curve records are identified by `EC1N41Ckb1h7d5e80d3c4d0` and `EC1N131Ckb1heb5f1998f20b`. The N41 inputs are the first three raw pair states of the frozen public relation audit. The N131 inputs are sums of the first six raw leaves from the frozen five-pair group control. Both target reciprocals were constructed by summing those three pair points; these controls verify the equation, not natural query yield. The [audit result](audit_result.json) records exact encoded inputs and roots.

The arithmetic-only native-XOR comparison fixes the same target reciprocal in each field and uses the same `KaratsubaCircuit` multiplication. It excludes source-mask constraints, solver time, and group replay.

| Field | Core | Free intermediate input bits | AND gates | XOR rows | Clauses | Total circuit variables |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| N41 | Two S3 links | 41 | 2,826 | 2,439 | 8,560 | 5,429 |
| N41 | Direct S4 | 0 | 5,652 | 4,024 | 16,997 | 9,799 |
| N131 | Two S3 links | 131 | 17,451 | 15,567 | 52,615 | 33,542 |
| N131 | Direct S4 | 0 | 34,902 | 26,224 | 104,837 | 61,519 |

The direct circuit saves one field element of input freedom, while adding 2,826 AND gates at N41 and 17,451 at N131. These counts are from [circuit_counts.json](circuit_counts.json). Build wall times on this unisolated host are diagnostics only. `candidate_id` remains `null`: this is a target-conditioned point-decomposition gate, not a complete IC candidate or a one-target online comparison.

## Source-constrained N41 public query

The next gate used all 125 usable W8 masks from the frozen N41 geometry, three raw pair outputs, six distinct masks, and the existing folded-column collision shield. Both formulas used the same public point `(920359962848, 755404565011)` and reciprocal target `1000731834126`, with zero Frobenius rotations. The [source protocol](source_protocol.json), [formula counts](source_build_result.json), and [solver protocol](source_run_protocol.json) freeze the inputs, source code, formulas, solver binary, order, 120-second parent cap, 4 GiB sampled RSS cap, and one worker.

| Public formula | Source AND gates | Total AND gates | Total variables | Formula bytes | Solver status at 120 s | Sampled peak parent + solver RSS |
| --- | ---: | ---: | ---: | ---: | --- | ---: |
| Two S3 links | 2,397 | 5,223 | 9,197 | 356,474 | `BOUNDED_UNKNOWN`, wall cap | 94,568,448 B |
| Direct S4 | 2,397 | 8,049 | 13,580 | 548,451 | `BOUNDED_UNKNOWN`, wall cap | 82,313,216 B |

Neither solver produced a terminal SAT or UNSAT line before its cap. The [paired run receipt](source_run_result.json) retains both raw statuses and output hashes. These wall times are exploratory because this host has no isolation receipt; the child CPU time was substantially below wall time in both runs. No solved-query timing ratio follows from these censored rows.

The positive control fixes the six masks and three reciprocal pair outputs from the independently verified N41 group relation. Checked Sage supplied the intermediate reciprocal and independently checked the three-pair sum in [source_control.json](source_control.json). Both pinned formulas returned SAT in about 0.06 seconds. The [model checker](control_model_result.json) verified all 16,471 clauses and 3,777 XOR rows of the two-link assignment, and all 24,866 clauses and 5,362 XOR rows of the S4 assignment. These are correctness controls under different, constructed target coordinates, not natural public-query yield.

## Run statuses and next gate

The first audit wrapper failed after launch because macOS denied recursive process-tree sampling; [launch_failure_v1.json](launch_failure_v1.json) preserves that infrastructure status. V2 passed the mathematical assertions and then failed JSON serialization of a Sage `Integer`; its raw stderr and [receipt](audit_run_v2.json) are retained. V3 converts that one output value to a native integer and saved the full successful result. The first pinned-control builder then rejected a count comparison across different target constants after writing both formulas; [its failure receipt](source_control_build_failure_v1.json) preserves the error and hashes. V2 compares the identical source prefix, and the resulting formulas and models were checked. Earlier protocols remain immutable.

The source-constrained comparison is now complete at its declared cap. A further S4 SAT run should first reduce the 8,049-gate N41 circuit or expose a source-aware cut that prunes masks before the full resultant circuit is built. A useful next experiment would share the pair-product subexpressions between the exact source equations and the target equation, then freeze the resulting circuit and repeat the paired public query with the same source and cap. Promote only a verified group relation from an unpinned public query; retain this capped pair as the baseline for that gate.
