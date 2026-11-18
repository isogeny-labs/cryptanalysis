# Curve25519 representation archive: storage and evidence qualification

- **Status:** open
- **Kind:** access limit; proof and experiment-qualification gaps
- **Affected work:** [research archive](../research/curve25519-representations-20261117/README.md), PR #1728
- **Next action owner:** artifact-store owner for access; future admitted research runner for scientific qualification
- **Last updated:** 2026-11-17

## Problem

The exploratory archive cannot yet be fully delivered through the repository's artifact store because the bucket client returns `AllAccessDisabled`; its scientific assertions also lack signed independent PCC verdicts and the current preregistration/identity records. [pcc:unverified]

The user's immediate request is to create a PR for the previously delivered Curve25519 representation report, scripts and results. This branch preserves reviewable sources and exact pending-file hashes; the broader request to establish an improved index-calculus algorithm remains open. [pcc:unverified]

## Evidence and uncertainty

- **Observed:** the unchanged artifact tool's `push --jobs 1` returned `HeadObject: 403 Forbidden` on pending object hashes; the focused AWS client check of the same bucket in `us-east-2` returned `GetBucketLocation: AllAccessDisabled`. A normal STS call resolved the configured identity. This distinguishes a storage access failure from a missing CLI or absent runtime credentials. [pcc:unverified]
- **Preserved:** [pending inventory](../research/curve25519-representations-20261117/pending-artifacts.json), original [digests](../research/curve25519-representations-20261117/original/SHA256SUMS), source code and report source. No successful remote upload/readback is asserted. [pcc:unverified]
- **Derived or proved:** no new scientific theorem is established by this import. [pcc:unverified]
- **Missing capability:** permitted bucket access; a frozen successor protocol/export, canonical identity/route registration as applicable, faithful formalization and signed independent scientific checks. Historical scope notes cannot be retroactively promoted to preregistration. [pcc:unverified]
- **Limit:** a local timeout or bounded lift scan establishes neither a general obstruction nor a security theorem. A second producer-written arithmetic path is not a signed independent verdict. [pcc:unverified]

## What would unblock it

- [ ] Restore permitted access to `s3://setec-astronomy-artifacts/store`; unchanged artifact `push`, remote byte checking and clean-checkout hydration must succeed for every pending file. [pcc:unverified]
- [ ] Preserve the original data unchanged and publish real generated store manifests; do not fabricate locations or weaken the artifact gate. [pcc:unverified]
- [ ] For scientific promotion, file a current protocol before new affected data; bind exact field/curve/subgroup/base/route/code records, retain failures, and obtain the required independent signed verdicts. [pcc:unverified]

Storage restoration would complete the archive-delivery requirement only. It would not establish a performance improvement or resolve the research objective. [pcc:unverified]

## Next discriminating step

- **Action:** after access is restored, submit the exact inventory with `tools/artifacts/artifacts.py push`, then remote verification and clean hydration. [pcc:unverified]
- **Controls:** each original digest and byte count must match; a missing object, mismatched digest, denied operation or partial upload keeps the affected item pending. [pcc:unverified]
- **Limits:** no new search, benchmark, solver run or paid compute is launched by this import; no remote objects are overwritten or deleted. [pcc:unverified]
- **Outcomes:** successful storage closes only that access gap; a continued denial remains an access problem. Scientific qualification requires a separately admitted successor, not relabelling the archive. [pcc:unverified]
- **Recheck trigger:** owner/provider confirms bucket availability or a normal permitted client operation succeeds. [pcc:unverified]

## Resolution and history

2026-11-17: recorded during draft PR packaging after the normal store client and focused bucket-location check failed. The raw bundle and rendered report remain in the originating session workspace, with their hashes retained in the PR. Unresolved. [pcc:unverified]
