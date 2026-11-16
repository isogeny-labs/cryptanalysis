# Fixed-instance timing from prepared immutable executables

This is a separate timing attempt following the preserved run-001 build cap.
Use the same twelve frozen target workloads100..105, exact registered curves,
archived bases, sixteen candidate identities, four methods and matched rho
rules from PROTOCOL.md. The first attempt executed none of these workloads;
there is no observed algorithm output used to choose the targets or methods.

[pcc:unverified] Build preparation is governed by BUILD_PROTOCOL.md. Before timing, publish
prepared-input.json with the preparation job, exact source commit, receipt
SHA-256 and both executable SHA-256 values. The timing controller reads only
those named files from the preparation's retained Modal volume output archive,
verifies every hash and the candidate source fingerprints, and copies the
executables into its own output. No compiler runs in the timing allocation.
The preparation receipt/toolchain is retained with every timing output.

Use one L4 allocation,4 requested CPUs,8GiB and900-second hard cap. Pin one
allowed CPU;780-second controller cap and12-second per-process deadline remain.
Keep every per-arm cap and continue the frozen matrix. Preserve all source,
input, calibration and hardware snapshots. Before/after A/A, arm and method
orders, correctness and count checks are unchanged. The attack interval and
counted-S versus wall-derived equivalents are unchanged; report outer-process
cost separately. Prepared binary source may precede new analysis/prototype
source in the checkout; the immutable receipt and binary hashes identify what
actually executes. Do not build from a later checkout under an earlier ID.

All qualified values remain null on this unprepared gVisor host. Original
run-001 remains censored and immutable. No default activation or broad
performance claim follows from either preparation or raw timings.
