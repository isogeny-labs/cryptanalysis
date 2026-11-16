# Exploratory field-component panels

## Latest candidate: source757c0b1a71, fresh fixtures25..29

The output-extent candidate completed25 pairs at1m dependent field multiplies
per arm. Every checksum agrees and every calibration meets the frozen bound.
All qualified values remain null; the record is invalid for promotion.
PCC-20261116-109e4d binds the unsigned arithmetic report. [pcc:unverified]

| Degree | Limb width | Raw median default/candidate wall ratio | Observed five-input range |
| --- | --- | ---: | ---: |
|113|2(control)|0.97736|0.97009..1.20487|
|131|3|1.06532|1.05377..1.08592|
|155|3|1.06839|1.06513..1.07276|
|163|3|1.06207|1.04715..1.07117|
|233|4(control)|0.99325|0.99003..1.00019|

Both control medians are below1 and remain in the data. The three-limb raw
ratios are lower than the first panel's values. Fixtures and allocation also
changed, so these panels do not isolate the effect of consolidating the bounds
check. Fewer compiler-emitted checks do not establish lower wall time. The
single-check candidate stays opt-in, with no claim of being the fastest variant.
The benchmark protocol requires controlled timing before default activation.
[pcc:unverified]

Job20261116-035129-4194 completed with exit0 after31.2seconds. Its launcher
receipt reports the L4 allocation and its source/binary hashes and every arm
are retained under run-002 and launch-002. The isolated field tests are rerun
for both binaries before timing. assembly-002 retains ARM64 compilation and
unit/clippy logs: the three-limb branch contains six PMULL instructions and
one output-extent comparison. This is compiler evidence, not timing standing.
[pcc:unverified]

## Earlier candidate: source1a77f08668, fixtures20..24

The producer CUDA/L4-host panel completed25 paired dependency-chain runs,
with1,000,000 field multiplications per arm and five fresh input fixtures per
case. All checksums agreed and all25 before/after calibration ratios met the
frozen0.85..1.15 bound. Required placement evidence remains incomplete, so
every qualified value is null and the benchmark record is invalid for promotion.
PCC-20261116-302f23 binds the unsigned arithmetic report. [pcc:unverified]

| Degree | Limb width | Raw median default/candidate wall ratio | Observed five-input range |
| --- | --- | ---: | ---: |
|113|2(control)|1.00199|0.99930..1.00598|
|131|3|1.08313|1.08120..1.08829|
|155|3|1.08421|1.08273..1.08470|
|163|3|1.08197|1.08106..1.09129|
|233|4(control)|1.02360|1.01873..1.02547|

These are field-multiplication component ratios from a producer diagnostic.
They do not establish relation collection, full index calculus, novelty or a
matched-point IC/rho result. Keep the control shifts, including the four-limb
ratio1.02360; code layout, dispatch and allocation effects have not been
separated from the changed carryless-product count. A universal reduction in
wall time cannot be inferred from this allocation. [pcc:unverified]

The baseline uses default features; the candidate adds f2m-karatsuba3 to the
same isolated crate, importing the actual suite field module. Construction,
one independent schoolbook multiplication check and final checksum encoding
are outside the timed chain; runtime dispatch, scratch initialization,
reduction and result handling are included. Fields113/233 retain their
original multiplication path. Fixture indices20..24 and the controller were
published before the run. No production default is changed.

Job20261116-034333-6009 finished with exit0 after31.2seconds. The provider log
reports NVIDIA L4, four requested CPUs and8GiB. The CPU model is unknown and
the kernel identifies gVisor. The run-001 manifests pin all arm rows, source
and binary hashes, host observations and summaries. launch-001 retains the
provider log. assembly-001 preserves a native ARM64 compiler listing with
six PMULL instructions in the three-limb branch; instruction count alone is
not a timing or full-algorithm conclusion. [pcc:unverified]

The arithmetic/replay checks are producer reports. Signed standing, controlled
host timing and the full suite feature job remain open. The named broader
qualification problem is ../ic-native-current-20261115/REPORT.md and
../../problems/native-ic-timing-qualification.md. No allocation remains running
for this completed panel. The original broad performance goal remains open.

## Full-suite integration receipt

The isolated field module passes on ARM and Linux, but the full suite check
is incomplete. Its existing --locked resolution fails before compilation;
a normal offline resolution then fails in unchanged
bindings/rust/hashed-ecdl-tensor/src/structured_runner.rs:134 because the
digest return type lacks LowerHex. The upstream manifest reproduces the same
dependency error. The attempted resolved lock and every failed command log
are retained in integration-001; the suite lock was restored byte-for-byte.
No dependency upgrade is included. The full-suite feature CI step remains
required, and this issue cannot be counted as a field test pass.
[pcc:unverified]
