# Production binary-subtraction frontier

The new `subtract-binary-batch` oracle runs on the **actual production FastCurve backend** in both repositories. It reuses prepared negative operands and scratch buffers, shares inversion within blocks, and optionally finishes an ordinate only after the existing abscissa index admits a candidate. The previous tiny-field control remains unchanged and is not the frontier comparator.

Five targeted controls pass in each repository: 12,900 exact first-witness comparisons against general curve pair enumeration, 880 larger-field/re-preparation comparisons, 90 OpenSSL-backed comparisons, complete known-answer pipeline recovery, and failure/extra-lane accounting controls. These are producer observations, not signed independent verification or measured speedup. [pcc:unverified]

## Requirement status

| User requirement | Status and evidence |
| --- | --- |
| Continue beyond the fixture baseline | Production implementation and both CLI dispatches added; targeted native controls pass. [pcc:unverified] |
| PR in crypto | Extends https://github.com/isogeny-labs/crypto/pull/4335 |
| PR in cryptanalysis | Paired source on codex/binary-subtract-frontier-20261115; PR linked in the session log after publication |
| Preserve orientation/correctness | Exact scalar first witness, full-point membership, x=0/O/inverse/doubling and repeated-label controls; evidence/production-controls.log. [pcc:unverified] |
| Reach the speed frontier | **Open.** Protocol names native and external incumbents; no admitted timing result or fastest claim. |
| Broader tests/CI | Recorded separately from the five targeted controls; see session log and evidence. |

## Usage and accounting

Both IC CLIs accept:

```
--oracle subtract-binary-batch:m=2,block=32,lazy=1
```

Crypto also exposes the oracle through ecbench `ic.pipeline` / `ic.pipeline_full`. The production source is `src/cryptanalysis/ic_framework/binary_subtract.rs` in crypto and `suite/src/cryptanalysis/ic_framework/binary_subtract.rs` in cryptanalysis. These module bytes and their canonical native controls are mirrored exactly.

Parameters are strict: m must be 2; block is 1..4096 (default 32); lazy is 0 or 1 (default 1); unknown keys fail. Failed prepare invalidates the previous run. Default block size is provisional pending timings, not a selected optimum.

Preparation caches negatives and records their construction. Every target processes base indices in scalar order. A block can compute extra sums before an early hit; **all computed lanes** are charged to GroupOps. Lazy mode records x tests, actual ordinate completions and full-point probes separately; a successful x test alone never becomes a relation. Complete coordinates and keys retain the sign. No pair-sum table is allocated; memory is O(B + block), alongside the existing factor-base indexes. [pcc:unverified]

These are first-hit methods. The older complete-output fixture API returns every ordered pair and must not be used as a misleading latency denominator. Table-based frontier comparators have their cold construction included; their witnesses may differ and must be independently re-added.

## Native controls

```
cargo test --release --manifest-path research/binary_subtract_frontier_20261115/check/Cargo.toml -- --nocapture
```

The audit facade links the actual library. Its tests are the canonical `binary_subtract_tests.rs` beside the production oracle, also wired into the normal library unit suite. C++ and OpenSSL development headers are required for the external check. No custom field arithmetic is used in that helper.

Coverage includes every point of K0/K1 over GF(2^7), arbitrary sign subsets, empty bases, repeated labels, identity and finite x=0; full/lazy blocks 1,2,7,32,64; K1/n11, K1/n17, K0/n31 with blocks 1,8,32,128 and same-length re-preparation; exact extra-lane accounting; and known-answer pipeline recovery. Earlier fixture failures are retained: K0/n11 and K0/n17 do not meet the existing subgroup constructor's requirements, and a low-dimensional subspace did not have the size the early-hit control assumed. Valid curves and explicit generator multiples corrected those test setups without weakening assertions. [pcc:unverified]

The library/CLI check and targeted raw output are retained in evidence. After restoring tracked GPU and ECC catalog assets, the full cryptanalysis library suite passes: 3,075 passed, 90 ignored, zero failures. The initial seven missing-asset failures remain in evidence. Crypto's full release libtest compilation reached its 600-second build bound before tests ran; its focused production audit and library/CLI checks are separate evidence. [pcc:unverified]

## External OpenSSL edge case

On OpenSSL 3.5.7, the raw binary `EC_POINT_invert` path leaves `(1,0)` unchanged on `y²+xy=x³+1` over GF(128), modulus 131. The [primary source](https://github.com/openssl/openssl/blob/openssl-3.5.7/crypto/ec/ec2_smpl.c#L481) returns early when Y is zero. In this model the correct negative is `(1,1)`; `(1,0)` has order four, not two. The helper retains raw inversion under `--check-native-invert`. Its matched `--check` mode applies affine negation using OpenSSL `BN_GF2m_add`, then uses OpenSSL curve addition for every search. [pcc:unverified]

Reproduce after compiling openssl_control.cpp with C++17 and -lcrypto:

```
printf '7 131 0 1 1 2\n0 1 0\n0 0 1\n1 0 0\n' | ./openssl-control --check-native-invert
printf '7 131 0 1 1 2\n0 1 0\n0 0 1\n1 0 0\n' | ./openssl-control --check
```

Raw inversion returns `0 none` and `1 0 0`; explicit affine negation returns the correct `0 0 0` and `1 none`. Scope is this concrete edge/control; it is not a statement about every OpenSSL point or standard subgroup. See evidence/openssl-y-zero-control.txt and retained initial failure logs. [pcc:unverified]

## Frontier status and next action

[PROTOCOL.md](PROTOCOL.md) names scalar, full native batch, lazy block variants, cold negation-folded tables, applicable Frobenius layouts, external comparison and A/A. It freezes workload, costs and admission before measurements. Crypto's prospective frontier-panel.json uses the existing native ecbench route. Component n31 and external timed wrappers remain separate obligations, not completed measurements.

No experiment was launched. The current executor has no AWS identity or EKS connector; the actual STS credential failure is recorded in the preceding baseline study. Current budget/pool readback, L2 admission and cryptanalysis checkpoint custody remain required. [The named obstruction](../../problems/binary-subtract-speed-frontier.md) gives exit conditions. Continue from the frozen panel when those conditions hold; do not substitute local test elapsed time as speed data.

No leaderboard or canonical timing graph changes: no admitted timing dataset exists. The new explanatory diagram and report describe the production route and evidence. A claim to reach the frontier requires the actual incumbent comparisons and validation, including broader external review; passing tests or merging the PR does not establish it.

## Sources checked

- Both repos: native FastCurve batching/lazy kernels, Gf2, generic SubtractOracle, FactorBase indexes and pipeline stage contracts. Crypto additionally has paired SoA and AVX-512 paths, already present before this work; the new oracle calls the maintained dispatch. No novelty claim.
- Crypto: ic_framework/rootfind.rs, ic_run.rs, ecbench/methods.rs and IC technique catalog. Cryptanalysis: suite counterpart sources and native CLI dispatch.
- OpenSSL 3.5.7 ec2_smpl.c inversion implementation and actual libcrypto controls. OpenSSL is an independent arithmetic backend, not an independent signed verdict.
- Cryptanalysis build prerequisite: its binding declared getrandom 0.4 while calling the removed getrandom function. Updated to the declared version's fill API and refreshed the suite lock; the binding's 64 unit tests pass. [pcc:unverified]
- Sources checked (KB): unavailable in this runtime; both fallback wrappers have no executable. Source-level fallback across both repos informed the native backend choice; no absence, novelty or global fastest claim.
- Execution/report rules: crypto isolab-eks and research-visuals; cryptanalysis report-evidence/research-visuals and checkpoint policy. These preserve the original speed objective while admission remains unresolved.
