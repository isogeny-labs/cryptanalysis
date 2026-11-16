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

Full-suite integration remains incomplete because the unchanged digest
formatting dependency fails with the upstream manifest too; previous receipts
are in ../ic-f2m-three-limb-20261115/integration-001. Controlled timing and
signed standing remain open. The broad performance goal remains active.
