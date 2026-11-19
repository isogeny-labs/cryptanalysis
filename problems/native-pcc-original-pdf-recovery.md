# Native PCC original PDF recovery

- **Status:** `investigating`
- **Kind:** access/tool limit; original artifact custody gap, not a proved mathematical obstruction
- **Affected work:** [hosted PCC gate](https://github.com/isogeny-labs/cryptanalysis/actions/runs/44597234639); [exact missing-input receipt](../docs/audits/2026-11-19-pcc-original-input-custody-gap.json)
- **Next action owner:** T-7171 for bounded custody tracing; artifact-store owner for access restoration
- **Last updated:** 2026-11-19

## Problem

The native PCC gate lacks an exact original 92,135-byte PDF. Six other missing original objects were recovered losslessly; this PDF remains unrecovered while S3 is unavailable. [pcc:unverified]

The acceptance criterion remains the existing complete hydration, immutable content checks, proof verification and required CI. This note grants no exclusion, weakened gate, new trust key or claim standing.

## Evidence and uncertainty

- **Observed:** source revision `47a30653c4e2362af3d4ffe78237dec433df155d`; The original hosted hydration failure names seven missing objects. Six original cache objects, totaling 105,584 bytes, match every manifest hash and length and pass the actual CLI with an empty cache and no AWS executable. Recovery commit `0db5c8c621410b054cbae8a3949bb68d413885b1` is awaiting its hosted gate result. No assertion is made that restoring the PDF alone will make later verification pass. [pcc:unverified]

The original claim `PCC-20261114-03cfb7` and its custody record bind the PDF. The alternate historical Git path is an 83-byte symlink to the same missing canonical path. Bounded local searches checked 290 canonical-path roots and 287 alternate-path roots without finding matching bytes. These searches do not prove universal absence. [pcc:unverified]
- **Derived or proved:** no mathematical conclusion; no complete proof-verification result follows from successful hydration.
- **Suspected explanation:** the originals may exist in an unavailable store or another retained archive; their current location is unknown.
- **Missing capability:** readable exact original bytes from an approved retained copy or restored original store.
- **What this evidence does not establish:** absence from all history, invalidity of the underlying research, or success of later proof verification.

| Original path | Bytes | SHA-256 |
| --- | ---: | --- |
| `docs/research-artifacts/chained-transfer/arithmetic-audit-01/report.pdf` | 92135 | `eb814265f158fc0ad52d9306b5a2526da476bd40752c186d3918fa9b2d36279b` |

## What would unblock it

- [ ] Recover each listed original with exactly the retained byte count and SHA-256; preserve manifests, source records and existing copies.
- [ ] Hydrate through the existing verified artifact reader with an empty cache, then run the complete unchanged PCC gate on the final candidate commit.
- [ ] Resolve any subsequent verifier or CI failures separately; record the actual terminal result before merge.

Exact byte recovery is necessary to resume the gate. It is insufficient to establish a scientific result or successful downstream verification. Re-rendering a PDF, regenerating data, altering hashes or manufacturing replacements does not meet these conditions.

## Next discriminating step

- **Action:** inspect a specifically identified retained archive or original-store copy when one becomes readable; verify candidate bytes before installing them.
- **Inputs and controls:** the table above and the original manifests are authoritative; reject same-size wrong-hash candidates and leave their originals unchanged.
- **Execution limits:** no S3 probe while the owner says it is down; no new cloud resource or spend; no bulk history hydration. Check local space before materializing large candidates.
- **Outcomes:** an exact match permits verified hydration; a mismatch is retained as a failed recovery candidate; unavailable bytes leave the obstruction open.
- **Recheck trigger:** a new identified original copy, restored store access, or a terminal result from the already running recovery gate.

## Resolution and history

2026-11-19: recorded exact observed identities and bounded recovery evidence. Unresolved. Creating or merging this note does not close the gate or establish a research result. [pcc:unverified]
