# Parallel PCC appends block IC optimization integration

- **Status:** open
- **Kind:** immutable-ledger integration/custody gap
- **Affected work:** PR1621, native IC/S3 optimization branch; upstream PR1624
- **Next action owner:** repository PCC custodian; current performance work can continue
- **Last updated:** 2026-11-15 America/Los_Angeles

## Problem

The current main and optimization branch have different valid append-only PCC
suffixes after their common167-entry prefix, and the strict main-prefix gate
cannot accept both at once without an accepted reconciliation procedure.

## Evidence and uncertainty

[pcc:unverified] After fetching origin/main atd9ee51f206, the current main has
168 entries and the result-publication working ledger has184 (including two
new claims pending commit). The audit records the pre-publication Git head and
separately hashes the exact working ledger bytes. Both independently pass the
unchanged pcc.check_chain implementation. Main's next entry is a correction of
PCC-20261115-8d2645 from PR1624; the branch's next entry is its earlier arithmetic
claim. `pcc ledger verify --base origin/main` fails atindex167. The read-only
hash/count audit is archived at
experiments/ic-s3-pipeline-20261115/pcc-prefix-audit.json. Neither chain was
rewritten. Earlier prefix checks against main5dfcf82e69 passed.

[pcc:unverified] The owning AGENTS.md requires the base ledger to be a prefix and says:
"Never edit or rewrite pcc/ledger.jsonl." The available tool verifies prefixes
and appends claims but supplies no fork reconciliation command. A similar
cross-repository frozen-chain problem already appears in the problem index.
This does not establish a scientific obstruction or justify a gate exemption.

## What would unblock it

- [ ] An accepted custody-preserving procedure represents both original chains
      without silently rehashing, dropping or reordering historical entries.
- [ ] The resulting current-head ledger passes the actual unchanged prefix and
      hash-link gates against actual current main, or a separately reviewed
      trust-model change explicitly authorizes the reconciliation.

[pcc:unverified] No such procedure is implemented by this performance change. Do not reset to
main's ledger, re-create claims under new IDs, weaken the gate, force merge,
forge signatures or label the branch independently verified to hide this gap.

## Next discriminating step

Have the PCC custodian specify or implement the supported reconciliation, using
the two immutable Git heads and read-only audit. Keep the current source,
claims, benchmark records and raw measurements reviewable on the feature branch.
Native affine-oracle implementation and correctness work remain available and
do not require marking the broad performance goal blocked.

## Resolution and history

Unresolved. The feature's internal chain remains valid and preserved. Its
latest-main prefix check is explicitly failing, so integration is pending.
