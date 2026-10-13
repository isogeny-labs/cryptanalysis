# Q1358 ordinary public-target phi query: frozen 600-second receipt

The Q1358 phi-domain encoder produced the frozen official-public-point
formula byte for byte, and one CryptoMiniSat worker searched it under the
600-second and 4-GiB caps. The worker reached the parent wall cap with an
indeterminate solver state. The [terminal verifier](terminal_verification.json)
checked the raw logs, source hashes, one-worker resource envelope, and phase
sum. This preserves a complete ordinary-query solver receipt for the v3
15-summand phi-domain method.

| Quantity | Recorded value |
| --- | ---: |
| Curve | `EC1N131Ckb1heb5f1998f20b` |
| Workload | `3c1992b7c92f`, one published public point |
| Formula | 280,734 variables; 216,236 CNF clauses; 208,656 native XORs |
| Formula SHA-256 | `7c13f22d9a21a80475690436bee523027b2e75ee8dcf7d2e11a50148111cd619` |
| Target-dependent formula build and serialization | 9.359408417 s |
| Solver-stage wall time | 591.996523625 s |
| Charged partial query wall time | 601.355932042 s |
| Conservative combined RSS bound | 1,248,575,488 B |
| Solver terminal state | `indeterminate`, parent timeout, no model or SAT/UNSAT line |

The published point was supplied directly. Formula construction and all
solver work on it are included in the charged partial-query interval. Source
and accepted Sage runtime hashes, exact solver command, raw XCNF and solver
output, resource observations, and the full run record are retained beside
this note. The target was not decoded into a verified relation during this
bounded attempt, so complete online cost and rho ratio remain null.

CryptoMiniSat excluded the largest recovered XOR matrix: 44,369 rows by
46,211 columns exceeded the frozen 10,000-row limit. A separate frozen N41
public-query control tests whether admitting a smaller excluded matrix
improves a formula with an independently checked witness before changing
the N131 solver policy.
