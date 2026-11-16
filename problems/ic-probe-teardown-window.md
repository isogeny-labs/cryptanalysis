# The probe's recorded computation window omits teardown

- **Status:** investigating; explicit replacement clocks required before fresh timing
- **Kind:** measurement-boundary implementation gap
- **Affected work:** PR1621, ic_affine_pipeline_probe comparisons using context_ns plus RunReport.wall_seconds
- **Next action owner:** T-6450
- **Last updated:** 2026-11-16

## Problem

The old probe's internal elapsed value does not include all cleanup described by
its frozen protocols/reports as complete cold computation. It also does not
isolate the primary one-target online interval.

## Evidence and uncertainty

[pcc:unverified] Source audit20c68d: RunReport.wall_seconds is read while the
report is constructed, before function-scope factor-base/matrix destruction.
The probe's boxed oracle is dropped after JSON serialization. RhoResult.wall_ns
is likewise read before its local distinguished-point/jump-table teardown.
The controllers calculate their plotted value from context_ns plus these
internal fields, rather than an outer clock through cleanup. The value is a
recorded computation window, not complete cold. Whole-guest Callgrind Ir includes
executed process teardown and remains correctly scoped.

The existing scalar checks, input hashes, relation/matrix counts and raw numbers
remain. The original plots/records/claims are immutable; their complete-cold label
and interpretation require this correction. No estimate, process-wall substitution
or post-hoc addition can establish the missing intervals. Their already-null
qualification/invalid promotion status is unchanged.

This directly affects the recent prefix-scaling, inverse/matrix, compatible
PCLMUL and packed-square timing reports using that probe/formula. Earlier reports
using different probes need their owning timestamp audit before a scope claim is
transferred. It does not establish a regression or change any recovered scalar.

## What would unblock it

- [ ] An outer IC computation clock includes run_pipeline return and explicit
  oracle destruction before its end; context creation remains separately visible.
- [ ] An explicit target-compute clock spans matrix construction, target-dependent
  collector setup/query/matrix/scalar verification and owned-buffer cleanup.
  For the MITM study, audit that the preceding base/oracle preparation depends
  only on reusable field/base metadata before calling this the online interval.
- [ ] A symmetric outer rho clock includes all target-dependent setup, walks,
  scalar check and owned table/buffer destruction on the same point.
- [ ] Publish corrected source and freeze fresh controls/targets/accounting before
  timing. Retain previous evidence; do not reprice or relabel its raw files.

New clocks must be diagnostic fields, excluded from primitive operation pricing.
Independent arithmetic replay remains separate and its timing/accounting explicit.
[pcc:unverified] Passing source checks alone does not measure an improvement or qualify the host.

## Next discriminating step

Implement the explicit clocks before the next batched-collector comparison,
with the unchanged scalar collector and exact source/input controls. Verify the
new interval boundaries by source/ownership audit and fresh native receipts.
Report target-independent setup, one-target computation, independent replay and
complete computation through cleanup separately. Preserve every cap/control.

## Resolution and history

2026-11-16: Source discrepancy found while planning the next collector. Audit
claim20c68d is unsigned. Previous complete-cold descriptions are corrected by this
record and the linked erratum; original results stay immutable. Implementation
and fresh measured intervals remain pending.
