# CT201 — complete cold single-target ECDLP candidate-evidence gate

Protocol frozen 2026-11-18 UTC, before any real timing records. [pcc:unverified]

## Position in the transfer research programme

The original Chained ECDLP Transfers producer is [crypto #3877](https://github.com/isogeny-labs/crypto/pull/3877), merged. Existing benchmark components: [crypto #4215](https://github.com/isogeny-labs/crypto/pull/4215), [cryptanalysis #1523](https://github.com/isogeny-labs/cryptanalysis/pull/1523), [CT198](https://github.com/isogeny-labs/cryptanalysis/pull/1748), [CT199](https://github.com/isogeny-labs/cryptanalysis/pull/1756), and [CT200](https://github.com/isogeny-labs/cryptanalysis/pull/1761). CT198's exact 48-packet counter equality implies the norm-point saving **cancels** in direct-vs-retained, leaving only `C13a+C13b-C169` in the additive primitive difference. This gate separately requires the *entire* source-to-answer path and never promotes primitive timing to a solve-speed claim.

The original 695/701-record source custody, native 48-packet arithmetic parity and signed independent PCC remain blocked; last native typecheck attempted [CT200 Actions #44247758448](https://github.com/isogeny-labs/cryptanalysis/actions/runs/44247758448), stopped on original object-store HTTP 403. No replacement fixtures or simulated native results are admissible.

## Prospective offline input schema

Input JSON has **exact** keys `schema="ct201/full-cold-evidence/v1"`, `curve`, `memory_cap_kib`, and `runs`. `curve` has exact `p,a,b,r,G,Q`, an odd prime field of <2^64 elements, nonsingular short Weierstrass curve, prime-order generator subgroup `r`, non-infinity generator and public target `Q` in that subgroup. The checker independently verifies the affine curve equations, that `[r]G=[r]Q=O`, and each output scalar `0<=k<r, [k]G=Q`. No generator scalar is used to construct an algorithm input.

Exactly one *fresh process* record per block and algorithm `transfer, rho, rho_sham, bsgs, ic`, on one declared host, in 8 or more contiguous matched blocks, is required. Records must include the identical canonical curve-input SHA256, stdout and binary SHA256 strings (producer declarations, **not independently attested**), a declared host ID, external process wall nanoseconds, peak resident memory, complete scalar answer, and all seven serial phase nanoseconds: setup, transfer, relation_collection, linear_algebra, individual_log, verification, other. Each recorded phase must be nonnegative and the sum cannot exceed external process wall; all process overhead is still charged by the external total. The user-declared memory ceiling applies to every arm. All five arms solve the **same exact public target** in each block.

The comparator is strongest matched reference **per block**: `min(rho, bsgs, ic)`. It reports paired log ratios `log(T_fastest_reference/T_transfer)` and a fixed-seed 4096-resample percentile bootstrap 95% *diagnostic* interval on the geometric mean. It checks the `rho/rho_sham` A/A geometric mean is within 10%, as an explicitly prospective acceptance threshold. A source-only output can be `candidate_needs_external_signed_verifier` if lower bootstrap ratio >1 with A/A accepted; otherwise `no_qualified_advantage`. This diagnostic is **not a statistical guarantee** (small n, dependence and stopping can invalidate naive bootstrap coverage).

## Hard limits and failure criteria

The independent arithmetic check establishes correctness of *a reported scalar for the reported public target*, NOT that a solver actually executed or that the time/process/coldness/host, binaries, receipt hashes or map custody are authentic. Reject missing arms, altered inputs, invalid outputs, off-curve points, incomplete phases, duplicate block-arm pairs, different hosts, warm arms, Boolean numeric substitutions, exceeded declared memory ceiling, or non-64-bit primality claims. Do not interpret producer-provided hash strings as a signature.

No native benchmark runs here. A real performance claim requires verifying the **raw log files**, provenance and input binding via a separately built verifier and signed PCC, plus original corpus custody, exact CT125 transfer parity, genuine cold single-target complete source and transferred solves, calibrated memory and A/A/positive controls; scientific uncertainty and multiple-try selection must be addressed before calling baseline/candidate >1 a result. For p>2^64, a separately proved primality and group-law verifier is required; do not weaken this bound.

Original source, frozen roster and experimental workflow are unchanged. No new paid cloud expenditure or protected merge is authorized. Shared research-KB search service and the encrypted autoresearcher lab-contract plaintext were unavailable from this runtime; no general novelty or literature-completeness claim is made. [pcc:unverified]
