# PR 1104 inherited static-analysis failures

- **Status:** open
- **Kind:** inherited CI failures; artifact-pull implementation defect fixed locally
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
- **Suspected explanation:** the analyzer's individual findings need review;
  no general false-positive or tool-regression claim is made.
- **Missing capability:** no implementation limitation prevents the
  artifact fix. The remaining C/shell fixes fall outside the GHS research
  change and need their own reviewed changes or a corrected base.
- **Not established:** final-head hosted success, merge, global curve-family
  novelty, a transferred prime subgroup or recovered planted log.

## What would unblock it

- [ ] Hosted artifact workflow passes with the sparse-pull fix.
- [ ] Inherited static-analysis findings receive reviewed fixes and all
  required/applicable checks succeed on PR 1104's final head.
- [ ] Verify no blocking review or conflict, merge with an expected-head
  guard, and confirm the resulting merge commit.

Passing these gates permits the PR merge; it does not resolve the separate
[target and novelty problem](binary-cubic-gluing-target-and-novelty.md).

## Next discriminating step

- **Action:** push the sparse-pull fix with its failing/passing regression
  receipts, post the inherited failure evidence on the PR, and track CI.
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
