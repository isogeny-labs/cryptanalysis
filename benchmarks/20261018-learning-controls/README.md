# Bounded learning and program-search controls

The [combined report](report.pdf), [count graph](controls.svg) and
[evidence diagram](evidence-flow.svg) are copied from the
[source study](../../experiments/ideas_learning_20261018/REPORT.md).
The corresponding PNGs were rendered from these exact SVGs at 150 dpi using
Inkscape; original study PNGs used 160 dpi/default Graphviz output. No source
study file or result was modified.

These are shared-host, CPU-only correctness and count diagnostics. The learned
static WDSat order did not improve the paper control; the restricted group-law
program search selected the incumbent; empty-base classifier training rejected
heldout positives and is never wired into an oracle; whole-curve conformal
intervals are unbounded with only three calibration curves. No new invariant,
general solver exponent or end-to-end IC speedup is claimed.

[Registry verification](registry-verification.json) records recomputation of all
ten exported curve aliases, full UIDs and hash preimages with the repository's
metadata identity helper. The ten exact records were appended to
[curves.yaml](../../experiments/ic-candidate-catalog/curves.yaml); its previous
three entries are unchanged. This is metadata identity verification, not a new
mathematical certificate. Existing curve aliases with different field/subgroup/
generator metadata were not reused. [Registration source](register_curves.py)
preserves the write-once integration procedure.
