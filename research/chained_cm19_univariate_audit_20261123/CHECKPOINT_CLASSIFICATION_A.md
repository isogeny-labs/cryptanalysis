# Fixed-certificate unit verification checkpoint classification

This task builds a deterministic verifier for one completed public
certificate and runs that verifier plus exact corrupted-fixture regression
tests. It creates no new candidate/curve/field-search population, held-out
challenge, sampled workload, timing comparison or IC experiment. The
Rust compiler/linter and Lean kernel checks are ordinary build/proof
checks. Exact source/input publication and full readback precede them.
[pcc:unverified]

Owning AGENTS.md, section "Resume checkpoints in S3 before every run",
says: "A command that is not an experiment run may opt out with
CHECKPOINT_SKIP=<reason>." Its experiment-launch S3 gate therefore does
not apply to this fixed-certificate unit verification. The thin caller
will carry that explicit reason. No S3 upload or experiment-gate pass is
claimed, and no credential, provider, canonical gate or policy is changed.
The user's requested durable checkpoint is the exact GitHub source and
whole-byte readback. This classification does not authorize a later
experiment/benchmark or exempt any source/limit/custody/CI check.
[pcc:unverified]

Stop on a real canonical hook rejection rather than changing identities,
budgets, admission criteria or verification rules. Retain its diagnostic
and proceed only with work outside the rejected command's dependency.
The original EKS/paidSTOP and actual experimental S3 requirements persist.
[pcc:unverified]
