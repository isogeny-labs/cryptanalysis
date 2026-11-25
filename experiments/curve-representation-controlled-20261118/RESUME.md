# Resume: controlled curve-representation comparison

## Goal
Execute the user's controlled growing-instance comparison, retaining time per usable relation, RSS, rejection, timeout, rank and full/censored collection cost.

## Lead / hypothesis
Equivalent coordinate systems may change the cost of solving relation equations. This is a descriptive stage experiment, not a new security or speedup claim.

## Spec
experiments/curve-representation-controlled-20261118/protocol.json and PLAN.md. Fixed fields, seeds, limits, same-base and query controls are in source. Protocol must be frozen and committed before new affected inputs.

## State
Source preparation only; fixed-fixture unit controls run. No scientific panel, held-out inputs or new timing dataset has been produced. S3 bucket access check returned AllAccessDisabled; no checkpoint token is configured. On 2026-11-18 the user instructed: "Upload to git". Git is the authorized checkpoint destination for this task. This instruction does not by itself establish CPU/GPU execution admission.

## Next steps
Source unit checks and protocol freeze are complete; retain the checkpoint in PR #1767. The frozen protocol SHA-256 is d30f250e5d237c9e8bd399ebea313289aa08e803affd15a2e38facba33eae738. Before running the scientific panel, resolve execution-host admission under the repository instructions. Git checkpoint storage is authorized; do not borrow another task's execution waiver.

## Runs in flight
None. Unit tests are foreground validation only; no panel is scheduled.

## Stop and success conditions
At most 132 cells, at most 24 ordinary queries each, 2 seconds per PDP, 60 seconds per collector. Complete collection requires rank and scalar replay. Retain all censoring/failures. No qualified speedup on an ordinary host.

## Open questions
Execution-host admission remains unresolved. Preserve the original acceptance criteria. No paid allocation or CPU execution exception is recorded by the Git-upload instruction.
