# Prospective N131 preparation yield decision

The independently audited, wholly prospective 23-query panel now meets its
frozen operational stop rule. Queries **10–32** each completed as an
ordinary `timeout` with zero verified relations, a checked 4-GiB RSS gate,
and preserved XCNF and solver-output hashes. The read-only v4 auditor returned
`RECOMMEND_STOP_AFTER_AUDITED_ZERO_YIELD_PANEL`; queries 1–9 are excluded
from the prospective statistical panel. The exact candidate and workload
identities remain in the [frozen gate protocol](../n131_d13_m12_precompute_futility_20261115/protocol_v4.json).

The [decision snapshot](decision.json) binds the first 32 append-only attempt
rows by SHA-256, the auditor and protocol hashes, its complete output, and
the live supervisor's PID, creation time, command, and child at capture.
`python3 verify.py` rechecks the immutable prefix and reruns the independent
auditor. Capture did **not** signal the runner or edit its runstore. At
capture, the supervisor had already advanced to query 33; its later rows
are outside the frozen 23-query panel and must remain preserved if the
runner is stopped.

The operational rule requires at least 1,098 productive preparation queries
among the candidate's 8,192-attempt limit, assuming the maximum four
relations per productive query. Under the protocol's explicit independent,
constant-rate Bernoulli model at that minimum rate, a 23-query zero-yield
panel has probability **0.03652**. This is a conditional sampling decision,
not a mathematical bound on the fixed published point or all possible
decomposition algorithms. The exact arithmetic and Lean status are in the
[gate result](../n131_d13_m12_precompute_futility_20261115/RESULT.md).

**Owner decision prepared:** stop this specific local supervisor and its
matching solver child after rechecking the PID creation time, command,
run ID, and latest append-only rows, then save a separate censored terminal
sidecar and retain all completed and in-flight artifacts. The frozen gate
explicitly makes the auditor read-only and authorizes no automatic process
termination. Until approval, the runner continues under its original
protocol; this decision record does not change the IC candidate or count as
a completed one-target timing result.
