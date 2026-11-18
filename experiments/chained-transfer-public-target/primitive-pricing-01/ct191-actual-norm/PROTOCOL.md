# CT191 — exact norm-point arithmetic versus the historical D proxy (prospective)

2026-11-17 UTC · [pcc:unverified] · `research/ct191-actual-norm-primitive-20261117`

## Research problem and non-overlap

The CT125 norm-reuse evaluator increments one `transported_norm_doubling` counter while executing `descend_point(curve::pmul(target.f,target.curve,&point,2))`. CT126 prices only `curve::padd(target.f,target.curve,&point,&point)` under label `D`. CT173 showed that these are **different source paths**: for k=2, the library `pmul` loop may execute two doublings and an identity addition before descent; machine optimization effects are unknown. In particular `D_padd` is NOT `N2_actual`. Source: `../CT173_NORM_POINT_PRICE_PATH_AUDIT.md`.

Keep the pinned CT126 source (`src/main.rs`, Git blob `ac4146577f5019fc17674deb342eb5d9fc749715`), historical output, CT125 native derivative, immutable 48/695/701 fixtures, and the parallel CT189/CT190 PRs untouched. Create a **separate, exact-source guarded Rust derivative** and an explicit source-only negative-test harness. No new algorithm, curve, or geometry.

## Proposed bounded implementation

1. Copy CT126 to a new package under `ct191-actual-norm/`, and preserve its original `C169`, `C13_first`, `C13_second`, `D_padd`, direct-warm and retained-warm arms and controls.
2. Add exactly one `N2_actual` warm arm that performs the **same mathematical code path as CT125**, `curve::pmul(target.f,target.curve,&point,2)` followed by the same `back6` descent matching the original private `descend_point` for infinity and affine points. No replacement `padd`, no surrogate operation, no scalar log lookup, no counter-derived price.
3. Match all five original CT126 **toy public scalar fixture inputs** (1,2,17,12345,ELL-1), separately check `N2_actual` against `D_padd` followed by the exact descent and each final curve's admission and route agreement. Preserve 4 warm-up + 12 measured blocks; reverse operation order each block; include actual raw timing, setup time and available VmHWM. Use `black_box` on results. Explicitly label output `ct191-exact-norm-warm-price/v1`.
4. Build-path provenance is a separate task: only an authorized owner-installed Rust/cargo toolchain and the restored pinned sibling crypto tree can compile and time this program. Static source tests must compare the derivative against the exact historical Git blob, verify only the specified modifications, and reject mutated norm code, dependency and timing labels; Python normal and -O. Never execute native Rust in CI.
5. No EKS Spot/GPU, GH Actions native workload, unapproved budget, protected merge, scoreboard, historical fixture edit or purported runtime measurement. Source CI and synthetic/source mutation results are not independent PCC.

## Essential scope limits and follow-on gate

The five precomputed CT126 operands **do not represent the whole 48-selected packet grid or the 695/701 original corpus**, especially exceptional half/correction sectors and the reverse direction. Therefore even a future native CT191 run cannot price every branch or establish a cold source-prime ECDLP advantage. It is a controlled instrument correction and preliminary warm arithmetic price only.

The next experiment must use the **original frozen 48 public packets**, extract the *actual* pre-norm post-map target operands without scalar disclosure, use full 21-counter/19-word native parity and authorized same-host paired `C169,C13a,C13b,N2_actual,D_padd` timings, including cold setup and memory. Only then use the authenticated full 695/701-record evidence and compare complete cold single-target recovery to strongest rho, BSGS and IC, with all setup/transfer/linear-algebra/inverse/verification/RSS, uncertainty, independent replay and signed PCC. Ratio baseline/candidate >1 must be reproduced, not assumed. If slower, record negative and move to next unblocked lead.

The norm-point source is `fixed-jacobian-chain-evaluator-02/derived/lib.rs` Git blob `b80eb91a39ae1e87f0fcde95e52ea3d3634558bc`; the original CT126 price source blob is `ac4146577f5019fc17674deb342eb5d9fc749715`. Reference PRs: [crypto #3877](https://github.com/isogeny-labs/crypto/pull/3877), [crypto #4215](https://github.com/isogeny-labs/crypto/pull/4215), [cryptanalysis #1523](https://github.com/isogeny-labs/cryptanalysis/pull/1523), [CT189 #1729](https://github.com/isogeny-labs/cryptanalysis/pull/1729), [CT190 #1732](https://github.com/isogeny-labs/cryptanalysis/pull/1732), [GPU IC #4178](https://github.com/isogeny-labs/crypto/pull/4178). [pcc:unverified]
