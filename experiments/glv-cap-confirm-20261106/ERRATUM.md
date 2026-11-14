# GLV cap confirmation: interpretation and evidence status

This note supplements the frozen [protocol](PROTOCOL.md), [report](REPORT.md), and
[results](results.json). It does not alter the protocol, rows, analysis, or
historical verdict. Source revision audited: cryptanalysis
`71b028679303b24123a9ac7afe7696e3143ee206`.

## Correction to the report's no-worse interpretation

The report says that the candidate "does no harm" for the `j = 0` family
because no `j = 0` cell interval is wholly above 1. That conclusion does not
follow from the registered test. The protocol's no-worse check **fails only if**
a 98.75% interval for a *size pooled over both families* has lower bound above
1. Passing it means this test did not detect a size that is wholly worse by
that criterion. It neither establishes a non-inferiority margin nor shows
`j = 0` is unharmed. The reported `j = 0` pooled estimate is 1.0020 with 95%
interval [0.9860, 1.0187], which includes both benefit and harm. The pooled
eight-cell H1 result and its registered decision rule are unchanged.

This is an interpretation correction, recorded as producer claim
`PCC-20261108-6081a3` with standing **unverified**. [pcc:unverified]

## What the current audit checks

- The selection and confirmation `PROTOCOL.md` SHA-256 digests match their
  respective `PROTOCOL.sha256` files.
- From the published confirmation cell point estimates, the primary geometric
  mean, both family means, and four size means recompute to the values in
  `results.json` within floating-point tolerance; the registered verdict
  flags follow their published interval endpoints. Selection bootstrap
  threshold probabilities sum to 1. Every published cell point estimate lies
  inside its listed 95% interval. These are checks of **published aggregate
  arithmetic**, not a recomputation from experiment rows. [pcc:unverified]
- The current source's `analyze.py` implements the protocol's ratio of paired
  operation sums per cell and independent within-cell bootstrap. Its table-cap
  formula matches the C selection logic in candidate commit `e71ebec`.
  This is a source inspection, not proof that the historical binaries or rows
  came from those sources. [pcc:unverified]

The 18 named `rows_*.jsonl.gz` files and two PDFs across the selection and
confirmation rounds are absent at the canonical SHA-256 object-store keys
listed by their manifests (all 20 returned 404 in a 2026-11-08 readback; a
known object returned 200). The six GitHub Actions runs associated with each
result commit contain coverage and CUDA artifacts, but no named raw-row
archive. The reports already say the rows and PDFs are absent from Git.
These observations **do not prove absence from every archive**. The original
archive location remains unknown, so row-level correctness, curve identity,
paired-arm custody, bootstrap recomputation, and figure/PDF regeneration
remain unverified. [pcc:unverified]

Local audit receipts retained for source inspection are
`/var/tmp/cryptanalysis-glv-aggregate-consistency-20261108.json`
(SHA-256 `90922c19a700184b5e8de0c3987ad873e69a22c326acfb1cc35a31c0c0fefcaa`)
and `/var/tmp/cryptanalysis-glv-custody-audit-20261108.json`
(SHA-256 `7eeabbb99b7dad065eb18ffc0406a303e44f7bfd49c628aa2a0c1ef135cd18c5`).
These host-local receipts are not a durable raw archive. The existing
`ratios.svg` parses as SVG and contains 13 plotted points, but regeneration
from `chart.py` fails on this host's Python 3.9.25 with
`SyntaxError: f-string expression part cannot include a backslash` at line 29.
The figure remains historical output; source portability needs a separate
repair and byte-for-byte regeneration check. No measured value was changed.
A regenerated PDF must await the original rows and an independent replay.
