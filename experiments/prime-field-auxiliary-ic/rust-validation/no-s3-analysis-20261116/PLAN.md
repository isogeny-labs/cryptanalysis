# Source-only analysis CI without S3

User instruction: **Proceed without S3.** The immediate failure is N83
`analysis-gate-tests` artifact restoration on PR #1536. Retain the failed
provider job and all earlier evidence; replace the unnecessary prerequisite
with an explicit checkout of the actual tracked unit-test inputs.

| Requirement | Implementation and acceptance |
| --- | --- |
| Execute the analysis gate without S3 | Run its existing eight test cases using only the nine tracked source/protocol/schedule files in a fresh directory, with network/subprocess access denied during Python execution. |
| Preserve validation | Keep the original analysis/test SHA-256 pins and test bytes; require checksum success and all eight tests. A missing frozen input and a changed pinned source must still fail. |
| Preserve artifact consumers | Add opt-in per-job dependency calculation; each actual data consumer must retain a generated pull. Shared metadata remains conservative; unsupported scoped structure fails. Test new dependencies, stale bootstraps, conditional checkout and legacy behavior. |
| Retain hosted gate and experiment semantics | Keep job name, PR triggers, test cases, the experiment job's dependency on the analysis gate, historical restore and non-PR condition. No check is disabled or waived. |
| Preserve research scope | Core, CLI, frozen snapshot, historical results and signed/unsigned evidence are unchanged. No runtime or fresh benchmark claim follows from these development checks. |

Validate the artifact utility's complete regression suite and global workflow
wiring, then run the actual source-only job commands and refusal controls.
Retain commands, source revision, complete outputs, exit codes and digests.
Append a producer integration claim, push the concrete correction, and retain
guarded auto-merge subject to every current-head CI/review condition.

The user has waived S3 as a prerequisite for continuing work. Git and the PR
retain this increment. This does not turn existing development fixtures into
a fresh performance experiment, supply an admitted measurement host/panel, or
establish auxiliary-map speedup. The random/special/same-base comparison and
supplementary rho remain the original research deliverables.
