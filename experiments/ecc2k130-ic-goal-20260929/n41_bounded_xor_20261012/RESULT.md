# N41 ordinary-point selection gate for bounded XOR projection

The cap-64 projector reduced the frozen N41 W4/m7 ordinary-point XCNF to
26,061 residual XOR literal occurrences, compared with 50,225 under complete
CNF-private XOR elimination. An independent certificate replay checked all
9,055 pivots and 10,569 row additions. The saved known public-point
assignment satisfies the projected formula, reverse-lifts to the original
formula, and matches the frozen full assignment exactly. The paired unpinned
solver screen reached its 240-second cap with status `CENSORED_TIME` and zero
model lines, so this method did not enter an ordinary-relation full pipeline
under the frozen budget.

The curve is `EC1N41Ckb1hf5a3eea408f4`, workload `2fa2f1e7c5fc`, with
98,400 usable factor-base points before folding, 1,200 folded columns, and
seven summands. The original public-point formula is SHA-256
`4823c390318388f4bfdd9d8dd09b28af49b8ddb89f21afdc685496992c1279a0`.
The same source, one-worker solver seed `2026100905`, 4 GiB combined RSS
limit, and 240-second parent cap were used for the new screen and the
earlier full-projection screen. Both are exploratory on a shared host.

| Frozen ordinary-point formula | Variables | CNF clauses | XOR rows | XOR literals | Widest intermediate row |
| --- | ---: | ---: | ---: | ---: | ---: |
| Original | 49,464 | 170,671 | 13,097 | 39,045 | — |
| [Full projection](../xor_projection_20261009/n41_public_v2/result.json) | 40,237 | 170,671 | 3,870 | 50,225 | 349 |
| [Cap-64 projection](public_cap64/result.json) | 40,409 | 170,671 | 4,042 | 26,061 | 64 |

The cap-64 [independent audit](public_cap64/independent_audit.json) replayed
every certified pivot from the original XCNF, compared the complete
residual XOR multiset and mapped CNF clauses to the emitted file, and
checked the known assignment through projection and reverse lift. The
projector and its checked Lean pivot proof are preserved in the
[N131 method directory](../n131_d13_bounded_xor_20261012/RESULT.md). The
new projection completed in 0.644 seconds locally; this shared-host wall
time is an algorithmic diagnostic, not a controlled speedup.

| Same ordinary point and solver policy | Status | Solver wall | Combined peak RSS | Model lines |
| --- | --- | ---: | ---: | ---: |
| [Earlier full projection](../xor_projection_20261009/n41_unpinned_run_R1/independent_terminal_audit.json) | `CENSORED_TIME` | 240.218 s | 173,539,328 B | 0 |
| [Cap-64 projection](public_cap64_stage_R1/independent_terminal_audit.json) | `CENSORED_TIME` | 240.057 s | 236,748,800 B | 0 |

The [frozen protocol](public_cap64_protocol.json) binds the formula, source,
projector, auditor, solver binary, runtime receipt, seed, command flags, and
prior paired receipts by SHA-256. The [raw solver output](public_cap64_stage_R1/cryptominisat.stdout.txt)
is retained. Its final restart line reports approximately 2.247 million
conflicts, versus 0.612 million in the earlier full-projection trace. These
are solver search diagnostics from two censored runs. Relation yield requires
verified models. The stage
receipts classify both runs by cap rather than by a mathematical absence of
decompositions.

The result selects against spending another N131 600-second ordinary-query
budget on the cap-64 projection alone. The next method gate is a
target-conditioned condition coupling at least two unresolved first-half
pair outputs with suffix outputs, as motivated by the
[N41 exact suffix-span result](../n41_output_first_inverse_20261012/RESULT.md).
It should preserve all 12 known eight-column public-point rows in that
frozen N41 control, reject complete first-half coefficient families before
source-mask enumeration, and report exact work and memory against the
completed 1,956-pair suffix join. Only a method clearing that smaller-field
ordinary-relation and full-pipeline gate warrants a new N131 prediction and
fresh ordinary-target query.

The three new Python modules parsed successfully. `go vet ./...` and
`go test ./...` passed from `orchestrator/` with local loopback access for
the test server.
