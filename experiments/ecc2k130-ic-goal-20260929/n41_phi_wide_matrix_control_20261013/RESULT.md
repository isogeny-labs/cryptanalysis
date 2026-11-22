# N41 public-query XOR matrix admission control

The frozen N41 public-target XCNF admits its previously excluded
5,335-by-5,768 native-XOR matrix when the CryptoMiniSat row and column
limits are raised to 6,000. The [terminal audit](audit.json) checks the
same formula and solver hashes as the earlier baseline, the exact command,
raw logs, admitted matrix, process drain, and resource cap.

| Same public point and source formula | Earlier default matrix limits | Raised 6,000-row/column limits |
| --- | ---: | ---: |
| Terminal status | `CENSORED_TIME` | `CENSORED_TIME` |
| Solver wall cap/elapsed | 120 s / 120.106 s | 120 s / 120.124 s |
| Sampled solver CPU | 18.233 s | 32.197 s |
| Sampled combined peak RSS | 83,869,696 B | 139,378,688 B |
| Solver model lines | 0 | 0 |
| 5,335-by-5,768 matrix | excluded | admitted |

The baseline and control ran on a contended host without a CPU isolation
receipt, so their CPU and wall figures are diagnostics of these exact
attempts. Matrix admission changed the solver's active XOR system but did
not produce a public-target model under the frozen cap. The larger N131
Q1358 matrix-policy change is therefore deferred. The next experiment
instead derives target-conditioned right-block coordinates and tests whole
source-product fibers before their Cartesian expansion.

The [protocol](protocol.json), [runner](run.py), raw solver output, [run
record](result.json), and [independent audit](audit.py) retain this
one-worker control. Candidate and complete online-cost fields remain null
because this is a point-decomposition solver-policy stage.
