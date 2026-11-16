# Artifact hydration and automatic step-factor audit

## Task
Continue the cross-repository semantic audit while the canonical artifact-tool owner PR completes CI. Preserve frozen experimental artifacts and land the native consumer through all applicable checks.

## Work
A direct public-API control with an infinite automatic grumpy step factor reproduced an undefined float-to-uint64 conversion under UBSan. Check finiteness and the exact 2^64 conversion bound before casting. Keep finite nonpositive defaults and explicit integer steps compatible; document that an explicit step bypasses alpha.

## Validation
Both ordinary and checkpointed entry points reject five invalid factors without changing the answer or operation count. Four finite/default controls and an explicit integer step with unused infinite alpha return the known scalar. All 21 ASan/UBSan CTest controls pass; the direct before/after reproducer stops reporting undefined behavior. Checkpoint bytes and frozen artifacts are unchanged. [pcc:unverified]

## Open threads
The canonical artifact source and its five regression methods follow the actual owner merge. Current owner source SHA256 is 5cad5ee04286bcd157cae3f2d6ae5ededf787645cfe3a471ed5584bc25c97c49. Hardware CUDA replay remains unavailable through the configured endpoints; existing tests and CI compilation retain their separate scope.

## Prepared canonical consumer
Copy the published owner source from c26d3bc61689c055c0e435f88e7258f4eefecbe2 byte-identically, along with its six focused methods and one lock digest. The current canonical digest is 35dfef67a6acda1184353d5e024ab850debfd404dd72241ed369be42daeaaa8d. All 29 native-repository artifact controls pass; 1,435 entries remain accepted and parity covers 16 shared files. Owner PR4393 must land first with this digest. Preparation before its merge follows the shared landing order; no consumer merge is authorized ahead of the owner. [pcc:unverified]

PCC witness inputs omitted by the sparse checkout were materialized from unchanged tracked Git files. Verify-all returns not_covered rather than a failed proof; unsigned statements retain their original status. [pcc:unverified]

## Evidence status and parity coverage
PCC-20261116-be9601 pins the native receipts and raw test logs as unsigned attestation data; its status remains not_covered. The initial consumer snapshot records the prior 16-file parity surface. Adding cryptanalysis to the artifact-tool lock membership now enforces that existing copy as well, and current parity passes across 17 shared files. [pcc:unverified]
