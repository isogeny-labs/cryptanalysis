# CT203 — prospective distinct-public-target complete cold ECDLP gate

Protocol frozen 2026-11-18 UTC before any CT203 candidate data or timing. Source-only construction. **[pcc:unverified]**

## Why CT201/CT202 are insufficient for a cold-solver claim

CT201 and CT202 validate the same declared target Q in every block. Even an independently witnessed execution of five binaries could then measure a candidate compiled with the solution to that one public challenge, rather than a general-purpose ECDLP method. Algebraic validation of [k]G = Q does not distinguish a solver from a precomputed or hard-coded scalar. This is a *possible protocol confound*, not an allegation that prior executables did this.

CT203 treats each row as a **single-target cold solve**, but repeats the comparison across **different** prospectively committed target points. Every method sees the same point within its matched block; successive blocks see distinct points up to negation. Retain the ten-block five-arm Williams order and same-binary rho/rho_sham guard of CT202. Do not replace or silently reinterpret any frozen CT201/CT202 evidence.

## Evidence schema

Exact top-level keys:
- `schema="ct203/fresh-target-complete-cold/v1"`
- `curve={"p","a","b","r","G"}`, short Weierstrass over a prime p < 2^64 and prime subgroup r < 2^64.
- `memory_cap_kib` (positive integer)
- `target_roster`: list of objects with exact `{"block":i,"Q":[x,y]}`, in block order, one per five-arm block.
- `target_roster_sha256`: lowercase SHA256 of the canonical JSON bytes of `target_roster` (sorted keys, compact separators, UTF-8). This is a producer digest, not authentication.
- `runs`: CT201's exact per-run record schema. Rows are **chronological** in contiguous five-row blocks, following the frozen ten-block CT202 Williams schedule (full cycles only). Each run's `input_sha256` is the canonical CT201 digest of `{"p","a","b","r","G","Q"}` for that block, not of the base curve alone. Each reported scalar must satisfy [k]G = that block's Q; all phase, external-wall, memory, cold-process and one-host requirements apply.

At least ten blocks and one full ten-block Williams cycle are required. Distinct Q and -Q count as the same target equivalence class: repeats up to sign are disallowed. Reject infinity, off-curve points, wrong subgroup, noncanonical coordinates, duplicate block IDs, missing arms, altered binary digests and mismatched rho/rho_sham hashes. Each arm must use one stable SHA-256 across every block.

## Scores and admission

Each block compares the transferred complete cold external wall against `min(rho,bsgs,ic)` for **that same block and target**. Report the paired geometric-mean ratio and a deterministic 4096-resample percentile-bootstrap diagnostic on blocks, plus A/A geometric mean and memory/uncounted wall. The same prospectively documented 10% A/A threshold is retained, and a lower diagnostic interval > 1 only yields `candidate_needs_external_signed_verifier`, **never** a verified speedup.

A genuine experiment must bind the challenge roster *independently after candidate source/binaries are frozen but before execution* and provide signed external custody of target generation, input bytes, executable hashes, process boundaries, memory, timings and stdout. A source-validated roster and self-declared SHA alone do not prove freshness or preclude a codebook hidden in a binary. Independent challenges should use an auditable external process that outputs points without supplying private logarithms to candidate operators; success still requires independent [k]G verification.

## Negative/control cases

Synthetic positive: ten distinct nontrivial public points on the p=97, r=97 toy curve, five identical-curve algorithms per point, strictly balanced order. Tamper cases: duplicate Q, negative-Q duplication, scalar for the wrong Q, wrong per-target input digest, reordered/partial panel, binary swap, rho-sham substitution, unsupported field size, malformed target roster digest and memory/phase accounting. Synthetic timing ratios must never enter a benchmark table.

Sources checked: crypto #3877 and #4215, cryptanalysis #1523, CT198 #1748, CT199 #1756, CT200 #1761, CT201/202 #1766, crypto #4178, 2026-11-18 session log and cryptanalysis AGENTS.md. The shared research-KB interface is unavailable here; no novelty/absence claim.

No native original 695/701 fixture, actual C169/C13/N2/D pricing, paid compute, independent PCC or complete ECDLP advantage is asserted. The existing S3 403 gate remains open. [pcc:unverified]
