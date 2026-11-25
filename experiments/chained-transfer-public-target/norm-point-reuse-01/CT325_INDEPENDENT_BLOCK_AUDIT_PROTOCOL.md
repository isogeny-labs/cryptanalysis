# CT325 — independent block-paired audit of CT324 cold rho controls

2026-11-22 America/Denver / 2026-11-23 UTC. **Retrospective, source-bound, [pcc:unverified].** This analysis is registered before writing the independent verifier, but after CT324 collected its original data; it is **not** a preregistered speedup experiment or new solver benchmark.

## Immutable source and exact scope

Review the active [cryptanalysis #1920](https://github.com/isogeny-labs/cryptanalysis/pull/1920) without touching its branch. Obtain the unmodified 24-child public **ct324-panel.json** from [CT324 completed source run 45104053819, artifact 14786980671](https://github.com/isogeny-labs/cryptanalysis/actions/runs/45104053819/artifacts/14786980671), uploaded 2026-11-23 03:07 UTC. The original artifact ZIP has SHA-256 `eb095b6d6eb29195ced78751fc6a220999c2765a6b49df9e1e9341e1ae6a56a9` (2811 bytes), extracted canonical JSON has SHA-256 `0ded77e0a6c955d27383b96d2aff128a680f32436328df199f385fd0ae2a5667` (14435 bytes). Do not substitute regenerated or selected records; abort on missing/unavailable artifact, digest, child, field, or mismatched canonical panel.

All 24 rows come from **four distinct public targets**, not 24 independent challenge instances: exactly two same-target cold children for each of three arms, in the prescribed ABBA-style order per block. CT322 BSGS and CT323 single-walker affine distinguished rho are unchanged controls; CT324 is 16-lane Montgomery-batched affine rho with a *different* distinguished-point threshold (1/64 rather than 1/16), so a difference cannot be assigned solely to batched inversion.

## Independent verifier, questions and controls

Implement one standard-library Python source-only auditor that does not import CT324 producer code. Require exact root, statistics, row schemas; original challenge SHA; four unique target IDs; six complete positions per block; stable per-arm binary digest; identical argv within a pair, different argv between targets; nonzero wall/RSS, legitimate counters and all source-record summary totals. Reject omissions, duplicates, swapped arm/order/target, changed totals, invalid counts, changed binary, corrupt checksum and malformed JSON. Report recorded parent outcome flags (zero original Jacobian executions, false strongest optimized rho, false complete transfer advantage, false independent PCC); these cannot be promoted.

Primary descriptive comparison: for each **target block**, first average its two wall times per arm, then report old/new and BSGS/new ratios; report the geometric mean of **four block ratios** (not the ratio of unpaired arm medians). Report the complete set of 4^4=256 four-block-with-replacement bootstrap geometric ratios and their nearest-rank 2.5% and 97.5% quantiles, explicitly labelled *exploratory* due to n=4/host/algorithm-dependent target stopping times; do not call them confirmed confidence bounds. Report the exact 16-pattern one-sided paired sign-flip sensitivity statistic **conditional** on symmetric, independent block null errors. Note that each pair has identical public Q and algorithm seed/walk profile; two cold processes are timing replication, not two statistically new ECDLP problems.

This is a separate **record-level** independent computation; source/public-checksum controls cannot verify the unavailable hidden scalar reveal, raw underlying executable stdout, actual independent native execution or signed PCC. Avoid reusing the existing single-run producer's summary as proof. Preserve unfavorable blocks and failed controls.

## Acceptance and next scientific gate

Accept this narrow result only if the actual original downloaded artifact passes unchanged SHA and every semantic check, normal Python and `-O` agree, and independently forged controls fail. The result can expose paired-target fragility of a provisional rho baseline; it is **not** an end-to-end index-calculus or transfer advantage.

Next: a prospectively registered 2+-host and >=16 independently drawn public-target control against the repository's strongest optimized negation-map/batch/SIMD rho, with explicit A/A, same walk distributions or separately decomposed distribution effects, source-verified logs, complete process wall/RSS/setup, and target-block uncertainty. Original E-to-J solver still requires authenticated frozen 695/701 plus 48 actual public packets, approved historical 6-object S3/STS and artifact-tool parity, physical `C169,C13a,C13b,N2_actual,D`, complete retained-lift/rho/BSGS/frontier IC single-target costs and signed PCC. Existing EKS paid STOP and merge/CI gates remain binding.

Sources checked: crypto #3877, #4215, #4178, #4715, queue #3904; cryptanalysis #1523, #1912, active #1920 and CT324 original reports; current AGENTS/ACTIVE and dated session logs. Research-KB MCP unavailable through this connector-only run. No new math theorem or novelty priority asserted. [pcc:unverified]
