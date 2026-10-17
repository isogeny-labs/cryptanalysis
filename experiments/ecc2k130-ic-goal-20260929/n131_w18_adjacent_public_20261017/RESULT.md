# Exact adjacent leaf on the frozen N131 public point

**An exact adjacent-Frobenius first join passed a complete ten-pair
Boolean control and an independent Sage point reconstruction.** On the
frozen W18 source, its two sign choices give 132,764 distinct first-join
reciprocals. The one-worker query on the frozen N131 public point ran
for 600.021632 seconds of target-dependent work and stopped at its
declared cap with status `BOUNDED_UNKNOWN`.

The first source edge is reused at rotations 0 and 1, leaving nine
independent source edges and 18 required distinct folded columns. For
source reciprocal (a=1/x(P)), first-join output (w), and sign bit
(e\in\{0,1\}), the new circuit enforces

\[
w(1+a^2+e a^4)=a+e a^3.
\]

The two branches give the reciprocals of (P+τ P) and
(P-τ P) exactly. The [proof map](PROOF_MAP.md) records the
algebraic derivation and checked Lean declarations. The prior
[N41 relation and N131 root audit](../n41_n131_adjacent_frob_leaf_20261017/RESULT.md)
are the unpinned control and source gate. A further
[source census](source_census.json) shows 66,382 distinct plus outputs,
66,382 distinct minus outputs, and zero overlap in this frozen table.
This is an empirical exact count of the finite source, rather than an
estimate of public-target relation yield.

## Frozen control and public query

The curve is `EC1N131Ckb1heb5f1998f20b` over
`GF(2)[t]/(t^131+t^13+t^2+t+1)`. The public point is
`(1052727368764798954359115163823647684025,
2071227447786120917960296877345506689833)`, workload
`cc09e7eb202a`. The [protocol](protocol.json) fixes the full source
dependency hashes, target, 524 raw-fiber/Frobenius choices, one solver
worker, 600-second target-dependent cap, 4-GiB sampled combined-RSS
cap, and CryptoMiniSat flags before control and query. The
[checked Sage runtime](sage_runtime_info.json) was saved first.

| Formula | Variables | AND gates | CNF clauses | Native-XOR rows |
| --- | ---: | ---: | ---: | ---: |
| Constructed adjacent control | 251,188 | 166,145 | 508,035 | 80,286 |
| Ordinary public query | 251,167 | 166,141 | 508,023 | 80,269 |
| Prior linked gap-16 constructed control | 250,823 | 165,875 | 507,226 | 80,191 |

The [constructed assignment](control_result.json) satisfies every
control clause and XOR row. The independent [Sage control](control_sage_audit.json)
rebuilds all ten signed source pair points and their raw sum, checks
the adjacent first join, and verifies that cofactor-four transport
lands in the prime subgroup. The adjacent control costs 270 more AND
gates and 365 more variables than the prior gap-16 linked control;
the first-join constraint trades circuit size for a more specific
equation. These are formula profiles, not a solver-speed comparison.

| Exclusive public-query phase | Seconds |
| --- | ---: |
| Four raw fibers and target orbit | 0.088294 |
| Formula construction | 3.197437 |
| XCNF serialization | 0.013024 |
| Solver launch, search, and stop | 596.720503 |
| Terminal parse | 0.002373 |
| **Target-dependent total** | **600.021632** |

The solver logged 6,199 restart rows. The parent stopped it at the
600-second sampled deadline; the 22-ms monitoring overshoot is included
above. Sampled combined peak RSS was 593,100,800 B. The solver exited
`-9` without a terminal SAT/UNSAT status or model, as retained in the
raw stdout and stderr and the [query receipt](query_result.json).
`BOUNDED_UNKNOWN` is a censored outcome for this exact cap. The
[independent audit](audit_result.json) checks the protocol, source and
target, complete formula counts and hashes, raw log status, all phase
costs and cap. The byte-exact [compressed formula archives](archive_result.json)
were replayed from their decompressed bytes, and the
[terminal verifier](verify.py) repeats that check. This was an
ordinary-host decomposition-stage run; `candidate_id` remains `null`
while the complete pipeline is unresolved.

The first `prepare-control` launch used system Python and failed at
`import psutil` before writing a fixture. Its retained
`prepare.stderr` identifies the environment error. The resumed
`prepare_v2` command used the repository's checked Sage launcher and
passed; that startup event is outside the target-dependent interval.

## Next algorithmic test

The unpinned N41 public relation used the same signed source pair
point in both adjacent slots. Restricting the first join to
(P+τ P) removes the sign selector and the second branch. The
exact first-join constraint becomes (w(1+a^2)=a). Run a frozen
constructed control and N131 public query for that source family,
with the reduced 66,382-output source count and any change in relation
density reported alongside formula size and the full attempt cost.
Any returned model still requires independent signed point replay
before it enters factor-log rank and single-target online accounting.
