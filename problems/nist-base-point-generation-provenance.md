# NIST base-point generation provenance

- **Status:** `investigating`
- **Kind:** unknown cause; access/tool limit
- **Affected work:** [base-point origin report](../docs/reports/2026-11-18-nist-base-point-origins/REPORT.md), [frozen protocol](../docs/reports/2026-11-18-nist-base-point-origins/PROTOCOL.md), draft PR #1769
- **Next action owner:** unassigned
- **Last updated:** 2026-11-18

## Problem

We cannot yet establish the source of the sample base points for P-224,
P-256, P-384, P-521, B-163 through B-571, or K-163 through K-571 because the
standards publish no selection procedure and no exact historical generator has
been reproduced for them. A retained bounded RNG search is additionally
blocked by the repository checkpoint gate in this environment.

The acceptance criterion for provenance is an exact generator, initial
seed/state, encoding and selection rule reproducing the complete published
`G=(Gx,Gy)`. For a bounded negative search, the acceptance criterion is a
retained run with positive controls and exact bounds; that narrower result
would not establish impossibility.

## Evidence and uncertainty

- **Observed:** FIPS 186-2 Appendix 6 §1.5 calls each supplied `G` a “sample
  base point” and gives no generation rule. Anthropic publishes exact FreeLIP
  code, six seeds and six exact `Gx` matches for P-192 and five X9.62 examples.
  Its article says the later prime and binary points remain unexplained.
  [pcc:PCC-20261118-9f025b; pcc:PCC-20261118-edcdea; standing: unverified]
- **Derived or proved [pcc:unverified]:** A published curve seed cannot be assumed to generate
  `G`; the standards specify a SHA-1 curve-coefficient construction separately
  from the supplied point. Koblitz curves have no random curve seed.
- **Suspected explanation:** another historical library point constructor,
  another position/encoding in the recovered RNG stream, a separately seeded
  generator, or manual selection. No alternative is preferred by current
  evidence.
- **Missing capability:** `scripts/checkpoint.sh gate` cannot upload because
  neither `CHECKPOINT_UPLOAD_TOKEN` nor AWS profile `ecc-challenges-new` is
  available. The repository research-KB executable/catalog is also absent.
- **What this evidence does not establish:** it does not show that the unknown
  points were generated randomly or deliberately, does not exclude an RNG
  rule, and does not reveal any challenge scalar.

## What would unblock it

- [ ] Restore a valid checkpoint upload token or permitted AWS profile, pass
  the gate, and execute the exact bounded run in `PROTOCOL.md` with all six
  positive controls.
- [ ] Obtain historical source, notes, or a reproducible algorithm that exactly
  matches each unexplained `Gx` and its `Gy` root choice.

The first condition permits a scoped rejection of two specific hypotheses.
Only the second can establish affirmative provenance.

## Next discriminating step

- **Action or proof obligation:** run the frozen same-stream `lrand48` and
  seed-derived SHA-1 search, then add a separately frozen normal-basis binary
  coordinate search if it misses.
- **Inputs and controls:** exact FIPS coordinates/seeds; six FreeLIP controls;
  polynomial and, in the successor, normal-basis coordinates.
- **Execution limits and stop condition:** the current protocol scans through
  the published stream endpoint plus 50,000 updates and counters 0…65,535.
  Stop at the frozen bounds and report exact matches only.
- **Outcomes and next actions:** a hit requires full point/root-rule
  reconstruction; a miss rejects only the frozen encodings; checkpoint failure
  leaves the experiment unrun.
- **Recheck trigger:** restored checkpoint access, recovered historical source,
  or exact normal-basis coordinate tooling.

## Resolution and history

Unresolved. On 2026-11-18 the implementation and protocol were prepared, but
the mandatory checkpoint upload failed before the retained experiment began.
