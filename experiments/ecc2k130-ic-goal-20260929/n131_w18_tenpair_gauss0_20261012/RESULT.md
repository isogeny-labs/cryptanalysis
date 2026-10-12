# Matrix-disabled CryptoMiniSat preserves the ten-pair N131 formula and reaches its cap

**On the identical frozen ten-pair N131 public-point XCNF, setting
`--maxnummatrices=0` removed every matrix-disable diagnostic but the ordinary
solver search reached the 600-second wall cap with `BOUNDED_UNKNOWN`.** The
baseline solver printed 3,202 such diagnostics and ended `s INDETERMINATE`
after 584.728 seconds of solver search. The variant recorded zero diagnostics,
2,957 actual restart rows, and a sampled combined RSS peak of 495,828,992
bytes. Both results are exact terminal receipts on the same formula and
public point; the local CPU timings are exploratory on an unisolated host.

The [frozen protocol](protocol.json) binds the parent ten-pair source,
constructed control and ordinary XCNF raw hashes, checked N41 relation,
solver binary, public workload `cc09e7eb202a`, one worker, 600-second wall
cap, 4-GiB combined RSS cap, and the sole changed solver option. The
[native-XOR smoke](smoke_result.json) verified both a satisfiable and an
unsatisfiable XCNF under that option before either full run. The parent
[constructed assignment](../n131_w18_tenpair_binary_frob_20261012/control_result.json)
satisfies every clause and native-XOR row; with the changed solver option,
the full constructed formula itself returned `s INDETERMINATE` after a
63.824-second solver interval under its 60-second internal cap.

| Same XCNF, public point, one worker | Default matrices | `--maxnummatrices=0` |
| --- | ---: | ---: |
| Ordinary XCNF SHA-256 | `7832bf557829605e97945df5fa984e57a7df014b214b8b5923d7b83c997d79a0` | identical |
| Formula variables / clauses / native-XOR rows | 258,801 / 528,856 / 81,074 | identical |
| Solver interval | 584.728336 s | 600.017239 s, runner wall cap |
| Sampled parent-plus-solver RSS peak | 607,961,088 B | 495,828,992 B |
| Actual `c rst` rows | 4,901 | 2,957 |
| Matrix-disable diagnostics | 3,202 | 0 |
| Terminal | `s INDETERMINATE` | runner `TOTAL_WALL_CAP`, no terminal line |
| Classified result | `BOUNDED_UNKNOWN` | `BOUNDED_UNKNOWN` |

The matrix-disabled [control receipt](control_result.json) and
[ordinary receipt](ordinary_result.json) record decompression outside each
solver interval, flags, wall, restarts, sampled RSS, stdout/stderr hashes,
exit code, and stop reason. The original ordinary attempt additionally
charged target orbit, formula construction, serialization, and terminal
parse to its 588.515-second target-dependent interval. The two solver
intervals answer only the same-formula solver-policy question; neither is
a complete single-target IC online measurement. The [audit](audit_result.json)
replays raw formula hashes from the parent's deterministic gzip archive and
checks the exact status lines and diagnostics. The [verifier](verify.py)
checks the smoke, protocol, receipts, and audit.

This policy change removed the noisy Gaussian-matrix behavior without
producing an ordinary relation under the frozen cap. The next algorithmic
test should return to a target-conditioned **joint constraint on unresolved
partial sums**: the valid N41 right-suffix outputs already span every
linear and quadratic output-only reciprocal feature, so a successful gate
must use cross-sum structure or a stronger representation. Freeze unpinned
positive and negative N41 families, measure whole-family rejection before
source-mask expansion, then make an exact N131 600-second/4-GiB projection
before another public-point query. The full IC candidate remains at
`candidate_id: null` while relation yield, useful rank, factor logs, scalar
recovery, and same-point rho accounting are open.
