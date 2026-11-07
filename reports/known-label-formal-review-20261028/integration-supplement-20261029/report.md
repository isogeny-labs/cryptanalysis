# Known-label integration review supplement — 2026-10-29

Producer: 5b20d2a705601327877f708655f37b92bc762da8. Reviewer: TASK-20261029-9058ad. This supplements the historical packet in cryptanalysis PR1285; it does not replace its original reports.

## Observed software validation

The independent J3 reviewer found the integrated verifier holds within trusted-tool and stable-workspace assumptions. All26 existing tests passed. All46 independent mock cases matched their expectations:40 refusals and6 acceptances. The accepted cases were two valid baselines plus four disclosed trust-boundary probes. Counts3/5 reject and4 accepts; all six persistent project mutations reject; qualified names, source/pin mutations, audit failures and unknown paths reject; both workflow filters cover the lockfile. These are software controls, not native proof execution.

The coordinator verified all11 reviewer artifact hashes and reran the pinned independence checker:PASS for the three declared joints. J1/J2 attestations remain historical source-level evidence. Two README files changed on main, so those old reports do not review the new documentation or printed elaborated types. The post-dispatch plan clarification preserves that limitation.

## Explicit limits

Python accepts fabricated successful auditor output containing a contradictory FAIL line or forged ok axioms. The actual native auditor's source returns failure for bad axioms; these probes identify trust in that process, not a demonstrated acceptance of a false Lean theorem. Transient source/project changes restored before final hashing are also accepted. Workspace stability and the pinned toolchain/cache remain assumptions.

The prior producer0b353c9bf passed native job123003327508 for all four unchanged ring identities and its positive/negative controls. That receipt does not establish native success for the integrated producer5b20d2a. Current-head CI is pending separate inspection. No independent elaborated-type comparison is archived. The broader graph/group, recovery, probability and performance claims remain open; no validated_scoped or full-task completion label is claimed.

## Provenance and next action

Prospective integration plan: commit1aa4e3e26. Additive bookkeeping correction:6ea69879d. The reviewer source manifest binds ten producer files; all fifteen allowed source files remained unchanged. Report SHA-256:202b1c151be8a02cdd75989644a22e1798a5c039bf7901202b379737f2e56309. The unchanged algebra source is d0e0fa1892bc800999e3b5330f543bf2e99811f607606901f363fce27bcb428d.

Conductor T-765 exhausted its fourth lease at03:17:05UTC after the reviewer outputs completed. Existing artifacts are preserved on durable storage. Publication of this final supplement needs a bounded archival follow-up; no review, experiment or native job needs to be restarted for archival. The report and diagram show verification states because there are no performance measurements to plot.

Evidence: cryptanalysis PR1284 and PR1285; native run40741310214/job123003327508; reviewer directory TASK-20261029-9058ad; artifact-hashes.json; independence-integration.json. GitHub links: https://github.com/isogeny-labs/cryptanalysis/pull/1284 and https://github.com/isogeny-labs/cryptanalysis/pull/1285.
