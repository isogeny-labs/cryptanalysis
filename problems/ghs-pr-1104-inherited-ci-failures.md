# PR 1104 inherited static-analysis failures

- **Status:** investigating
- **Kind:** reviewed main CI repairs integrated; final-head hosted verification pending
- **Affected work:** [PR 1104](https://github.com/aburan28/cryptanalysis/pull/1104), [CI evidence](../reports/ghs-pr-1104-ci-20261025/README.md)
- **Next action owner:** repository CI/C maintainers; PR author tracks final-head checks
- **Last updated:** 2026-10-25

## Problem

PR 1104 cannot merge while repository-wide analysis fails on unchanged base
C and shell inputs, despite successful Rust, Lean and ordinary CI checks.

The observed head is 099e8c53e1d98781270a451c1228859d48ea66fb against base
c5aa7b39bfa30e8cdbd46a158c7cbadaa8be3503. The user's gate requires successful
required checks; mathematical novelty and explicit DLP transfer are separate,
still-open research obligations, unaffected by this CI record.

## Evidence and uncertainty

- **Observed:** current-head analysis run 40165001420 failed shellcheck,
  clang-tidy, cppcheck and gcc -fanalyzer. Full decoded job logs and exact
  diagnostic/build-path identities are retained in the linked report.
- **Derived:** all 33 relevant tracked source/configuration blobs match the
  base exactly. No separate base CI run is claimed; source identity is the
  evidence for treating these diagnostics as inherited from the base inputs.
- **Observed:** artifacts run 40165001421 failed restoring a file into a
  directory excluded by sparse checkout. A regression fails on the old
  puller with the same missing-parent error. Creating destination ancestors
  fixes it, and all ten artifact-tool tests pass locally.
- **Observed:** the downstream workflow-wiring check also found a missing
  GHS hydration step, now added and passing its scoped check. The global
  check still fails for the unchanged `suite.yml`; its workflow and checker
  blobs match the base. This inherited wiring defect also blocks artifacts.
- **Observed, next head:** c5838032's artifact run 40168603888 passes hydration
  and all ten unit tests, then fails resolving an abbreviated object ID for
  a blob missing from its partial clone. A real blob-filtered local clone
  reproduces the error. Full object IDs fix it while still rejecting a
  90,000-byte JSONL offender; all eleven artifact tests pass locally. The
  [new receipt](../reports/ghs-pr-1104-ci-20261025/partial-clone/README.md)
  preserves the full failed job and regression outputs. Rust and both Lean
  checks pass at c5838032; ordinary CI and analysis are still queued.
- **Observed, hosted confirmation:** 8ffc01a1 passes ordinary CI, Rust and
  both Lean workflows. Artifact run 40172185678 passes hydration, eleven
  tests and the policy check; only inherited suite wiring fails. Analysis
  run 40172185776 repeats exactly the earlier normalized diagnostic sets
  (shellcheck 1, clang-tidy 38, cppcheck 34, gcc analyzer 1). Full logs and
  [comparisons](../reports/ghs-pr-1104-ci-20261025/hosted-confirmation/README.md)
  preserve this result. Of the 33-path inventory, only the intentionally
  fixed artifact tool differs from base; C/shell/analyzer inputs match.
- **Observed, main update:** main advanced through merged PR 1114 to
  d90192b5, repairing the inherited analysis and workflow-scanner issues.
  PR 1104 became conflicted. Integration a74d5404 resolves the equivalent
  full-object-ID conflict, imports all other main repairs unchanged and
  preserves historical GLV source evidence. All eleven artifact tests,
  global workflow wiring and the 96-source corpus pass locally. The
  [integration record](../reports/ghs-pr-1104-main-integration-20261025/README.md)
  retains exact inputs and the new versioned corpus receipt. Hosted checks
  on the final integration head remain pending.
- **Suspected explanation:** the analyzer's individual findings need review;
  no general false-positive or tool-regression claim is made.
- **Missing capability:** no implementation limitation prevents the
  artifact fix. The remaining C/shell fixes fall outside the GHS research
  change and need their own reviewed changes or a corrected base.
- **Not established:** final-head hosted success, merge, global curve-family
  novelty, a transferred prime subgroup or recovered planted log.

## What would unblock it

- [x] Hosted hydration and unit tests verify the sparse-pull fix (run
  40168603888); GHS scoped wiring also passes locally.
- [x] Hosted artifact policy succeeds with the full-object-ID fix (run
  40172185678), along with hydration and all eleven unit tests.
- [x] Reviewed main repairs are integrated; global workflow wiring passes
  locally, and imported C/shell sources match main exactly.
- [ ] All required/applicable hosted checks, including artifacts and analysis,
  succeed on PR 1104's final integration head.
- [ ] Verify no blocking review or conflict, merge with an expected-head
  guard, and confirm the resulting merge commit.

Passing these gates permits the PR merge; it does not resolve the separate
[target and novelty problem](binary-cubic-gluing-target-and-novelty.md).

## Next discriminating step

- **Action:** push the main integration and versioned source-binding replay,
  then track final-head hosted checks at spaced intervals.
  Do not push status-only commits for repeated unchanged failures.
- **Inputs and controls:** exact head/base blobs; original failed job logs;
  file-store sparse-checkout, corruption and round-trip unit tests.
- **Limits:** no broad C cleanup, suppression, gate bypass or paid compute.
  Do not repeat current-head CI polls within 50 minutes without new activity.
- **Outcomes:** green final-head checks permit a guarded merge; continuing
  inherited failures keep the PR open and identify the pending base fix.
- **Recheck trigger:** pushed head, new base/review activity, or next spaced
  scheduled check.

## Resolution and history

2026-10-25: CI logs inspected, inherited inputs compared, sparse-pull defect
reproduced and fixed locally with ten passing tests. Hosted verification and
inherited analysis remain unresolved. No failing check has been bypassed.

2026-10-25, subsequent local gate: GHS workflow hydration added; direct scoped
pull and wiring check pass. Global wiring still fails on the inherited
suite workflow omission. Earlier outputs and the initial CI manifest remain
frozen at 0cd35127, with the newer report/problem versions bound separately.

2026-10-25, 07:11 UTC: c5838032 verifies hosted artifact hydration and ten
unit tests, exposing a second partial-clone lookup defect in the policy
checker. Full object IDs fix a matching local regression; eleven unit tests
pass. Rust/Lean are green, ordinary CI/analysis queued, hosted policy fix
pending. Old manifests remain unchanged with explicit version transitions.

2026-10-25, 08:14 UTC: 8ffc01a1 confirms hosted hydration, eleven tests and
artifact policy. Rust, both Lean checks and ordinary CI pass. Inherited suite
wiring and identical static-analysis diagnostic sets still fail. Full logs,
source comparisons and explicit active-record transitions are retained.
The PR remains open; no unrelated C cleanup or gate bypass is performed.

2026-10-25, 15:06 UTC follow-up: merged main/PR 1114 provides the reviewed
inherited-gate repairs. Integration a74d5404 resolves the artifact-checker
conflict and retains every historical selector/negative control. Local
artifact tests, global wiring and 96-source corpus pass. The problem remains
investigating until final-head hosted gates and guarded merge are verified.
