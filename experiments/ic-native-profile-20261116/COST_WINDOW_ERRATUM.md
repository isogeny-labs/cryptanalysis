# Correction to the earlier cold-window labels

[pcc:unverified] Source audit20c68d finds that the earlier value named cold_wall_s
by the affine-pipeline controllers equals context_ns plus RunReport.wall_seconds,
which is read before some scope-exit cleanup. The boxed oracle is dropped after
probe output. RhoResult.wall_ns also precedes destruction of its local tables.
Those saved values describe a narrower recorded computation window. They do not
establish complete cold cost or the primary one-target online interval.

This correction applies to the recent prefix-scaling, inverse/matrix, compatible
PCLMUL and packed-square comparisons using this exact probe/formula. Their raw
ratios, controls, scalar replay, source hashes and unsigned/null qualification
are preserved. Previous complete-cold labels are overstated. No prior raw record,
report snapshot, claim or artifact is rewritten or re-priced. Complete cold ratios
remain unknown until measured with fresh explicit boundaries and frozen controls.

The profile002 whole-guest Ir captures include startup, output and executed
teardown; their instruction counts and attribution remain correctly scoped.
Their instrumented clocks are not native timings. See
../../problems/ic-probe-teardown-window.md for evidence and exit conditions.

The next source must expose separate reusable setup, target-dependent collector
computation and outer computation through oracle/matrix/buffer cleanup, with a
symmetric fresh rho interval. For MITM, audit that base/index preparation is
independent of Q before naming the collector interval the primary online metric.
Independent Python arithmetic replay is separate and must be stated as such.
