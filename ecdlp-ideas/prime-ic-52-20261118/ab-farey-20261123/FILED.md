# Filed: the two ledger rows

Filed 2026-11-24 into `docs/ic/boundary_targets.json` (schema_version 2) of
`isogeny-labs/crypto`:

**PR:** https://github.com/isogeny-labs/crypto/pull/5170 (branch `ab-farey-ledger`, one commit, `updated` + 2 records)

| stage | record | verdict |
|---|---|---|
| `regimes.prime.records.relation_yield` | `current` replaced, previous block pushed to `history` | `PRIME_YIELD_SHAPE_AND_TARGET_BLIND_EXACT_DISTRIBUTION` |
| `regimes.prime.records.factor_base` | `current` replaced, previous block pushed to `history` | `PRIME_AB_FAREY_BASE_O1_STREAMING_AND_INDEXABLE` |

## Claim-check receipts

Both PASS under `boundary_autolab.py claim-check --stage <stage>` at the filed
ledger revision (`schema_version: 2`, `fail_closed: true`, zero missing stage
fields, zero missing global provenance):

* `raw/receipt_relation_yield.json`
* `raw/receipt_factor_base.json`

The reports they validated are `raw/claim_relation_yield.json` and
`raw/claim_factor_base.json`, both generated reproducibly by `claim_ledger.py`
from the measured cells in `raw/`.

## What the rows claim, in one line each

* **relation_yield**: expected yield is `C(|F|+m−1,m)/|E|` for every base shape
  (counting identity, Lean-proved), and `r(R)` is uniform in the target off the
  base (88 buckets, max |z| 3.31); the only non-uniformity is `R ∈ F` at m ≥ 3,
  where `{R,P,−P}` forces `r(R) ≥ N/2`.
* **factor_base**: `|X(B)| = 4Φ(B) − 1`, mediant enumeration with no gcd and no
  set (4.2–5.5× fewer operations, O(1) memory), index-addressable at 58 µs on a
  10¹²-element base.

## Not claimed

Toy rungs (20/24 bits); no key recovery; no sub-rho claim; no claim that any
base shape or target statistic raises the expected yield.  The study's earlier
"target height law" is retracted in `report.md` §6 and is **not** in the ledger.
