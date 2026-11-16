# Artifact hydration and automatic step-factor audit

## Task
Continue the cross-repository semantic audit while the canonical artifact-tool owner PR completes CI. Preserve frozen experimental artifacts and land the native consumer through all applicable checks.

## Work
A direct public-API control with an infinite automatic grumpy step factor reproduced an undefined float-to-uint64 conversion under UBSan. Check finiteness and the exact 2^64 conversion bound before casting. Keep finite nonpositive defaults and explicit integer steps compatible; document that an explicit step bypasses alpha.

## Validation
Both ordinary and checkpointed entry points reject five invalid factors without changing the answer or operation count. Four finite/default controls and an explicit integer step with unused infinite alpha return the known scalar. All 21 ASan/UBSan CTest controls pass; the direct before/after reproducer stops reporting undefined behavior. Checkpoint bytes and frozen artifacts are unchanged. [pcc:unverified]

## Open threads
The canonical artifact source and its five regression methods follow the actual owner merge. Current owner source SHA256 is 5cad5ee04286bcd157cae3f2d6ae5ededf787645cfe3a471ed5584bc25c97c49. Hardware CUDA replay remains unavailable through the configured endpoints; existing tests and CI compilation retain their separate scope.
