# Gaussian admission gate for the N131 nine-pair circuit

Raising CryptoMiniSat's Gaussian matrix limits admits five 3,315×9,132 XOR
matrices from the frozen balanced nine-pair N131 formula. The unpinned
constructed-target control still reached its 120-second cap with
`BOUNDED_UNKNOWN`. During search, CryptoMiniSat repeatedly disabled Gaussian
elimination after reporting usefulness of 9.6825%, 11.7769%, and 17.5597%
for three of the admitted matrices. This tested the exact source matrices
that the default 2,000-row limit rejects, and it does not warrant spending
the 600-second public-point budget with these flags.

The [protocol](protocol.json) freezes the already archived constructed
N131 W18 nine-pair XCNF with all nine selectors free, the complete
18-distinct-column shield, and the balanced addition topology. The source
curve is `EC1N131Ckb1heb5f1998f20b`; the solver binary and original XCNF
are hash-bound to the prior [balanced experiment](../n131_w18_ninepair_balanced_20261012/RESULT.md).
The changed flags are `--maxmatrixrows=4096` and
`--maxmatrixcols=10000`; the solver's default maximum of five active matrices
was retained. One worker, 120 seconds of solver-stage wall, and 4 GiB
combined sampled RSS were capped before launch. The archived formula was
loaded and hash-checked before the solver-stage interval.

| Frozen control measure | Result |
| --- | ---: |
| Matrix rows×columns admitted | Five at 3,315×9,132 per initialization |
| Matrix initializations seen | 3 |
| Actual restart rows | 528 |
| Solver-stage wall / stop | 120.162 s / `WALL_CAP` |
| Peak parent-plus-solver RSS sampled | 677,117,952 bytes |
| Solver status lines / stderr bytes | 0 / 0 |
| Terminal classification | `BOUNDED_UNKNOWN` |

The [terminal audit](audit_result.json) replays the compressed source formula,
checks binary/source hashes and log digests, counts matrix admissions and
restarts, and confirms the wall and RSS classification. The constructed
assignment had passed all original clauses and native-XOR rows in the
source experiment; this solver run did not pin that assignment. The first
audit script attempt incorrectly assumed one matrix initialization and
aborted without writing a receipt; the corrected audit accounts for all
three initializations. The accepted Sage runtime was captured before the
run in `sage_runtime_info.json`.

This is an exploratory solver-stage gate on a constructed target, not an
ordinary-query yield or online-cost observation. Increasing only the row
and column limits did not make the constructed query tractable under the
frozen cap, while the solver's own usefulness guard disabled the newly
admitted matrices. The next experiment should change the exact
target-conditioned search structure, with an independently replayed N41
ordinary relation as its first control. `candidate_id` remains `null`.
