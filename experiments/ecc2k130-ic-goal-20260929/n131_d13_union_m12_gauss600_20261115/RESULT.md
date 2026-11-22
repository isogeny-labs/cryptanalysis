# Ten-matrix Gaussian arm for the ECC2K-130 twelve-leaf union formula

The [frozen Gaussian arm](query_protocol.json) activated ten XOR
matrices on the exact twelve-leaf official-point XCNF. Its
[result](query_result.json) is `BOUNDED_UNKNOWN` at the **615.088-second**
parent wall cap, with no terminal SAT or UNSAT line. Sampled combined
runner and solver RSS peaked at **2,117,779,456 bytes** under the
4-GiB cap. The [custody verifier](verify.py) passed.

The formula hash, public target, one worker, and resource limits match
the [default arm](../n131_d13_union_m12_query_20261115/RESULT.md).
The only solver-flag change raises the maximum Gaussian matrix size to
16,000 rows by 20,000 columns and admits up to ten matrices. The
[raw log](solver.stdout) confirms ten matrices initially active and
repeated later reports that Gaussian elimination was performing poorly.
The default arm also ended `BOUNDED_UNKNOWN` at 615.056 seconds while
using 681,639,936 bytes sampled peak RSS. Both are ordinary-host stage
diagnostics with other solver work live, so their wall times do not
establish a controlled performance ratio.

This arm tests the specific default-limit bottleneck: admitting the
small XOR matrices did not produce an independently replayable relation
under this cap. Raising the matrix count further has a weak cost case
from the observed low usefulness and higher RSS. The next algorithm
gate should demonstrate a source-valid, target-coupled rejection or
recovery method on a smaller-field ordinary instance, then carry its
exact work and memory accounting to this frozen N131 public point.
The complete IC proposal retains `candidate_id: null` pending a
verified ordinary decomposition and subsequent rank and target stages.

Run `python3 verify.py` here for the read-only custody check.
