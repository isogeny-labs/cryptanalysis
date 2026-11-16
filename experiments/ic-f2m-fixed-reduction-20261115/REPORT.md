# Fixed two-fold reduction: producer component evidence

Sourcead617a8a55 was published before fixtures30..35. The panel compares the
current default, six-product-only and six-product-plus-fixed-reduction arms
on the same inputs, in all six backend orders. There are six inputs per field,
1m dependent public multiplications per arm and30 triples. Every checksum
agrees and every before/after calibration meets the frozen bound.
PCC-20261116-3717ba is an unsigned producer arithmetic report; no signed
standing or qualified timing conclusion is claimed. [pcc:unverified]

| Degree | Default / combined median | Six-product / combined median | Default / combined observed range |
| --- | ---: | ---: | ---: |
|113(control)|0.93932|0.96087|0.93232..0.97277|
|131|1.34748|1.24228|1.34023..1.52746|
|155|1.31074|1.19881|1.30129..1.31708|
|163|1.46706|1.32854|1.45062..1.47511|
|233(control)|0.95117|0.95698|0.94610..0.95864|

Ratios exceed1 when the candidate takes less wall time. The control regressions
remain in the data and graph. The eligibility dispatch queries hardware before
excluding other widths; a width-prefilter edit is proposed for separate fresh
inputs. That source observation is not proof of causation for the entire
control shift. No result here establishes full relation throughput, end-to-end
IC performance, novelty or a matched-point rho comparison. [pcc:unverified]

The reducer handles canonical131/155/163 tails after a product of two masked
m-bit elements, whose degree is at most2m-2. With a one-word tail and m>128,
a high-part product and one remaining-overflow product finish reduction.
The131-bit top high word has at most two bits and uses masked XOR terms.
Mismatched element/field sizes, noncanonical polynomial representation, other
fields and unsupported CPUs preserve generic reduction. The feature is off by
default. Existing six-product multiplication remains independently selectable.

The native combined crate reports19 tests and clippy passing. Tests compare
every product-space monomial and4096 random bounded vectors per selected field
to bitwise reduction, plus generic fallback cases and the existing field
mul/square/inversion checks. The Linux allocation reruns16 default,17 six-
product-only and19 combined field tests before timing. These producer checks
support tested implementation behavior, not a formal Rust-to-field proof.
[pcc:unverified]

Job20261116-040611-a593 terminated exit0 after32.6seconds. The receipt reports
NVIDIA L4,4 requested CPUs and8GiB; the workload is CPU-only. Kernel is gVisor
and the CPU model is unknown. Required placement evidence remains incomplete.
All qualified values are null, and the benchmark record remains invalid for
promotion. run-001 and launch-001 manifests pin every raw arm, source/binary
hash, host snapshot, unit log and provider receipt. [pcc:unverified]

## Visual evidence and source history

[Arithmetic flow](flow.svg) is rendered from flow.dot. [Paired ratios](ratios.svg)
plots every input and the medians; ranges are observations, not confidence
intervals. render_report.py regenerates the SVG/PNG figures and REPORT.pdf
from the raw pairs. No canonical curve or isogeny-route edge changes: this is
a field-arithmetic adaptation without a new curve, map or subgroup claim.
The existing benchmark progress graph excludes this invalid record by policy.

KB source:4aeae310bd8926130ee38d08ce3d9da5, crypto:docs/perf/RESULTS.md at
d390e84ab2973372534120fc4207fb65e52d4f3f, describes prior two-fold reduction
for smaller Gf2 fields. The primary Git object was read. The mechanism is
known and its historical ratios do not transfer to this implementation.
The new multiword implementation and measurement scope are distinct.

At the original panel recording, the full-suite build failed in unchanged
digest formatting; those receipts remain in the preceding experiment. The
compatibility repair and current integration evidence are recorded below.
Controlled timing and signed standing remain open. The broad performance
goal remains active.


## Width-prefilter follow-up: sourceaf33968159, fixtures36..41

The follow-up uses the same three arms on the same inputs within each triple,
six inputs per field and1m calls per arm. All30 checksums agree, and no
calibration bound fails. PCC-20261116-2ecb15 binds the unsigned arithmetic
report. Qualified values remain null and the record is invalid for promotion.
[pcc:unverified]

| Degree | Default / combined median | Six-product / combined median | Default / combined observed range |
| --- | ---: | ---: | ---: |
|113(control)|0.94530|0.97209|0.94439..0.95118|
|131|1.33902|1.24308|1.33432..1.34836|
|155|1.28546|1.17411|1.27995..1.28959|
|163|1.45944|1.32104|1.44284..1.46517|
|233(control)|0.95951|0.96114|0.95343..0.96145|

The control regressions persist. The width edit has not eliminated that cost,
and changing fixtures/allocation prevents an isolated between-panel estimate.
Do not claim the prefilter has solved the regression or that the combined
feature is best for every field. Both the first panel and this follow-up are
retained. The feature remains off by default. [pcc:unverified]

[Follow-up paired graph](ratios-run-002.svg) and [PDF](REPORT-width.pdf) use all
raw triples; black bars are medians, dots are individual inputs. Neither plot
supplies a confidence interval or a qualified full-pipeline speed ratio.
Job20261116-041743-9ff7 exited0; provider and raw receipts are in launch-002
and run-002. The hardware/placement limitations remain. [pcc:unverified]

## Build compatibility and consumer checks

The declared sha2 0.11 digest output lacks LowerHex. structured_runner now
encodes each digest byte as two lowercase hex digits; the standard empty and
abc SHA-256 vectors pass. The suite lock is refreshed for the already-declared
sha2 dependency graph. Two compiler/clippy cleanups remove unused closure
mutability and use the crate's existing-MSRV divisibility method. No dependency
manifest is widened and no test or lint is disabled.

PCC-20261116-952977 records the producer integration statement. Inside the
full suite, all19 field tests pass; broader binary-ECC tests report54 passes
and one existing ignored test. That scalar_mul_by_order_is_identity test was
then invoked explicitly and passed, with3162 other tests filtered. The digest
known-answer unit test, combined-feature library clippy and default all-targets
clippy pass. integration-001/002 retain exact command output, including earlier
failed attempts. These are scoped consumer checks, not a claim that every
suite-wide test has run or passed. [pcc:unverified]

The timing crate imports only the field module and its locked arithmetic
dependency. Build-compatibility edits to the wider suite do not add work to
that measured interval. A full IC pipeline comparison, controlled host and
independent signed standing remain open.
