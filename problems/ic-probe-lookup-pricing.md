# Missing lookup units in archived IC probe model costs

Status: observed; repaired for the next probe panel, historical model caveat retained.

[pcc:unverified] An audit of four archived fixed-input studies found204 completed
IC arms with ns_per_lookup=0 and positive lookup/target-guard counters. The
framework prices these counters with that unit, so their model contribution is
zero. Group operations, native timed phases and matrix costs remain recorded;
the resulting counted-S/context-counted-S figures are partial models. They
must not support complete-cost or IC/rho model comparisons. The full cold wall
includes lookup work and is unaffected by this particular accounting omission;
its existing placement/noise qualification limits remain.

Reproduction: python3 experiments/ic-mitm-xonly-20261115/audit_lookup_pricing.py.
The output binds raw source hashes and per-arm counters. It reads the fixed
pipeline, native affine, column affine and full-point batch MITM timing-001 data.
All closed records, raw files and earlier signed/unsigned history are preserved.

The future x-only probe calibrates the lookup unit using the exact reference
pair table and freezes one calibration receipt per curve for all arms. Its
loader rejects zero required units and wrong curve identities; the controller
checks equality to the same archived units. A new panel is required to establish
its results. Do not backfill old rows from later calibrations.

This affects interpretation of producer statements ed23f0,2d1adb,2c490e,cf67bb
and a3e74d. An append-only correction claim and a source/data audit accompany
this problem record. No signed standing or general performance conclusion is
asserted. The broader performance objective remains open.
