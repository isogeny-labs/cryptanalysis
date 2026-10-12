# Matched matrix-policy gate on the N131 ten-pair circuit

**Disabling CryptoMiniSat Gaussian matrices removed all five admitted
small matrices and 164 matrix-disable diagnostics from the exact N131
ten-pair constructed-target search.** Both one-worker arms reached their
frozen 120-second outer cap while actively searching. The policy change
therefore removes this solver overhead, but this capped experiment does
not support promoting the flag to a 600-second ordinary-point run.

The source is the [verified ten-pair binary-Frobenius
circuit](../n131_w18_tenpair_binary_frob_20261012/RESULT.md) on
`EC1N131Ckb1heb5f1998f20b`, over
`GF(2)[t]/(t^131+t^13+t²+t+1)`. Its ten free W18 pair slots require
20 distinct folded columns. The source constructed assignment satisfied
all 528,850 CNF clauses and 81,064 native XOR rows; checked Sage replayed
the signed group sum and cofactor-four target. The exact 16,141,309-byte
XCNF was decompressed from the archived source and matched SHA-256
`68d25f14df34ff8eff90b759e99e77321276e4face1d3b8c58fd54230da6f401`
before either timed solver arm. Formula decompression is separately
recorded in `formula_prepare.json`.

The [protocol](protocol.json) froze the source archive and solver hashes,
the default-then-no-Gaussian arm order, one worker, 4-GiB combined RSS cap,
110-second solver flag, and 120-second outer cap before execution. Both
arms use `--threads=1 --maxtime=110 --zero-exit-status --verb=1
--printsol=1`; the second adds only `--maxnummatrices=0`. The outer cap
stopped each process before its solver-side time limit returned a terminal
line. The [audit](audit_result.json) checks exact command lines, parsed
native XOR counts, all six matrix initializations per arm, restarts, raw
log hashes, stderr, resource caps, and source receipts.

| Constructed-target solver stage | Default | No Gaussian matrices |
| --- | ---: | ---: |
| Matrices admitted at each of six initializations | 5 | 0 |
| Matrix-disable diagnostics | 164 | 0 |
| Active `c rst` rows | 1,432 | 1,213 |
| Child CPU service | 98.923 s | 91.563 s |
| Solver-stage wall to outer cap | 120.059 s | 120.022 s |
| Sampled parent-plus-solver peak RSS | 369,065,984 B | 451,035,136 B |
| Terminal classification | `CENSORED_TIME` | `CENSORED_TIME` |

Both arms reject the same 44,681 × 121,405 XOR matrix and nine
3,315 × 9,132 matrices under the default size limits. The default arm
then admits five small 52 × 356 matrices. The no-Gaussian flag removes
only those small matrices; it does not change the large rejected XOR
component. Host load rose from about 19 to 35 across the serial arms,
and child CPU service differed, so restart counts and wall times are
exploratory diagnostics rather than a controlled speed comparison.
The constructed input is a correctness and solver-policy control;
`candidate_id` remains `null`.

The decisive next algorithm step is to impose a target-conditioned
constraint that rejects multi-pair families before the final group-sum
search. A first implementation should preserve the independently verified
N41 ten-pair public relation, measure rejection and useful-rank behavior
on the frozen N41 point, and project source-bound N131 work and memory
under the 600-second/4-GiB gate before another full-width query. Merely
changing matrix admission has not cleared this preflight.

Run the read-only receipt check with
`python3 experiments/ecc2k130-ic-goal-20260929/n131_w18_tenpair_nogauss_20261012/verify.py`.
