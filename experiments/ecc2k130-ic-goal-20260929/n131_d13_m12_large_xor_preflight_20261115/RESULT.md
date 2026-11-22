# The N131 36,627-row XOR matrix fits the cap but stalls this SAT search

CryptoMiniSat admitted the previously excluded **36,627 × 38,097** XOR
matrix on the exact first d13/m12 ordinary preparation formula. The frozen
one-worker preflight reached its **120-second** parent cap with
`CENSORED_TIME`, 0 model lines, and **2,137,423,872 B** observed combined
parent-plus-solver peak RSS under the 4-GiB cap. Its last restart line reports
**24K conflicts**. The solver repeatedly logged `TODO disable matrix,
performing badly` after Gaussian usefulness fell near 11.6–13.4%. The
independent [terminal audit](large_matrix_R1/independent_terminal_audit.json)
confirmed the matrix admission, raw status, process drain, hashes, cap, and
memory. This preflight gives a measured reason to prioritize a target-coupled
decomposition filter over a full-budget run with this matrix setting.

## Frozen input and change

The input is the [saved XCNF](query.xcnf) from the first distinct
known-scalar preparation point in the live d13/m12 single-target candidate.
It is a uniform-scalar point fixture with the scalar withheld from the SAT
solver, not a planted decomposition. The exact curve is
`EC1N131Ckb1heb5f1998f20b`, workload `3c1992b7c92f`. The formula has
232,244 variables, 228,629 ordinary CNF clauses, and 171,278 native XOR
rows. Its SHA-256 is
`2c6d209f56e44314d5b90d3c55d7070813e8b49301da93a83d3845b1c7467f0b`.
The [source attempt](source_attempt.json) and decompressed formula hash
establish byte equality with the archived preparation query. The checked
[Sage runtime receipt](sage_runtime_info.json) was saved before execution.

The [protocol](protocol.json) fixes the formula, source attempt, runner,
solver binary, runtime, one thread, seed `2026100618`, 120-second parent cap,
and 4-GiB combined-RSS stop rule. Against the archived arm, the only solver
flag changes are `--maxtime=118.000`, `--maxmatrixrows=40000`, and
`--maxmatrixcols=85000`. The earlier row and column limits were 10,000 and
15,000; the parent and solver time caps differ by design for this resource
preflight. This is a PDP solver-stage diagnostic with `candidate_id: null`.

| Same formula and solver seed | Baseline archived arm | Large-matrix preflight |
| --- | ---: | ---: |
| Largest 36,627 × 38,097 XOR matrix | Excluded | **Admitted** |
| Parent wall cap | 600 s | 120 s |
| Observed charged query / solver-stage wall | 600.291 s / 598.776 s | 120.090 s solver-stage parent interval |
| Terminal status | `timeout` | `CENSORED_TIME` |
| Model lines | 0 | 0 |
| Last restart conflict field | 693K | 24K |
| Memory receipt | 2,395,668,480 B conservative combined bound | 2,137,423,872 B observed combined peak |

The [trace comparison](comparison.json) checks the saved baseline
[compressed stdout](baseline_stdout.txt.gz) against its archived raw-output
hash, parses both exact solver commands, checks the three changed flags, and
confirms the opposite matrix-admission decisions. The caps and memory
estimators differ, and the runs overlapped other work on an ordinary host;
the conflict fields are search diagnostics rather than a calibrated runtime
ratio. Both terminal rows remain preserved.

## Decision and next gate

The large matrix is feasible within the measured memory envelope. Its
120-second search trace supplies no reason to spend a full 600-second query
on the same setting: it reached 24K conflicts, ended at the wall cap, and the
solver disabled Gaussian elimination as poorly performing. The next method
selection gate is a source-bound target-conditioned constraint that rejects
admissible N41 code families while preserving the independently replayed
relation, followed by a 600-second/4-GiB N131 ordinary-query cost case.

Run `python3 verify.py` to recheck the protocol hashes, raw terminal audit,
same-formula comparison, and selected measurements. The [runner](run.py)
uses the repository's checked Sage launcher for local execution; the run
directory preserves raw stdout, stderr, process identity, and terminal
result.
