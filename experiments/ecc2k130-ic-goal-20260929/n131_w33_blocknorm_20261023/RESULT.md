# Exact block norm over N131 W33 first-code families

An exact target-conditioned block norm classifies a *set* of free first-code families with one polynomial GCD. On the frozen N131 W33 two-pair residual, a 16-code block produced GCD degree one for the constructed point and degree zero for the ordinary public point, agreeing with all 32 archived per-code GCD decisions. A scaling panel matched the independent first-code reference through 64 codes on both rows. The measured boundary is sharp: at 64 codes, the block norm took about 8.6 seconds per row while 64 individual GCDs took about 4.0 seconds. This degree growth rules out this direct batching as the early family rejection needed for the full relation search.

## Exact gate

For target-derived residual `T`, let `H_{T,p}(Z)=F_T(p,Z)` be the specialized quartic of the frozen 13-term two-pair resultant. For a finite first-product block `B`, define

`N_{T,B}(Z)=∏_{p∈B} H_{T,p}(Z)`.

The N41 right source is the 281 allowed W11 products, with explicit vanisher `A(Z)=∏_{q allowed}(Z+q)`. The N131 W33 right source is the 32-dimensional rotated product subspace, with linearized vanisher `L_V(Z)=Σ_{i=0}^{32}c_i Z^(2^i)`. The worker computes `gcd(N_{T,B}, A)` or `gcd(N_{T,B}, L_V mod N_{T,B})`. Positive degree means at least one first code in the block has a right-product root of the resultant. A zero specialized quartic is retained explicitly. The written proof and checked finite-product theorem are mapped in [PROOF_MAP.md](PROOF_MAP.md).

The N41 field is `GF(2)[u]/(u^41+u³+1)`; the N131 field is `GF(2)[u]/(u^131+u¹³+u²+u+1)`. Both use `y²+xy=x³+1`. Their exact curve IDs are `EC1N41Ckb1h7d5e80d3c4d0` and `EC1N131Ckb1heb5f1998f20b`. The N131 source seed mask is `898618`, with 32 free code bits and pair rotations `(0,18)`. The 16- and 64-code prefixes are raw first-code assignments; source eligibility and signed point replay remain later gates. Every artifact has `candidate_id: null` because this is a two-pair point-decomposition component.

## Frozen results

The N41 correctness gate used source-valid first codes in the frozen range `240..255`: seven codes survived source filtering. It retained `(253,63)` on the constructed residual and rejected the ordinary residual. Direct evaluation against all 281 allowed right codes agreed with both block decisions. Its corrected one-worker parent receipt records 2.880 seconds and 269,713,408 B sampled combined RSS under a 120-second/4-GiB cap. This is a fixed-block correctness control; it is not an unpinned full public-target relation search.

The N131 width-16 panel used raw first codes `0..15` and the exact 32-dimensional right-product subspace. It independently matched the archived checked-Sage per-code results: only first code `3` was retained on the constructed row, and none was retained on the frozen public row. The corrected one-worker parent receipt records 6.247 seconds and 277,970,944 B sampled combined RSS under a 590-second/4-GiB cap. The table contains exclusive GCD-stage times within that worker, after reusable field and right-subspace setup.

| N131 width-16 row | Block norm degree / GCD degree | Block GCD | 16 individual GCDs | Retained first codes |
| --- | ---: | ---: | ---: | --- |
| Constructed positive | 64 / 1 | 0.937 s | 0.964 s | `3` |
| Frozen public | 64 / 0 | 0.950 s | 0.955 s | none |

The separately frozen scaling run used prefixes `0..n-1`, sizes `4,8,16,32,64`, on both target rows. The target orders alternated: individual GCDs first on the constructed row, block GCDs first on the public row. All 128 per-code decisions matched the independent native reference, and every block decision equaled the disjunction of its prefix decisions. Parent wall was 37.447 seconds, with 325,074,944 B sampled combined peak RSS.

| First-code block size | Norm degree | Constructed: block / individual | Public: block / individual |
| ---: | ---: | ---: | ---: |
| 4 | 16 | 0.745 / 0.219 s | 0.738 / 0.218 s |
| 8 | 32 | 0.380 / 0.481 s | 0.381 / 0.471 s |
| 16 | 64 | 0.948 / 0.995 s | 0.934 / 0.985 s |
| 32 | 128 | 2.690 / 2.012 s | 2.696 / 2.007 s |
| 64 | 256 | 8.648 / 4.040 s | 8.553 / 4.045 s |

These are ordinary-host component timings. The small size-8 advantage is exploratory; the size-32/64 increase and the degree-256 modulus show that this implementation loses its batching benefit as the family grows. The complete public-point relation search also requires generating and checking every outer residual, distinct factor-base columns, point signs, and eventual relation rank. None of those costs is included in these GCD-stage cells, so no single-target IC or rho timing ratio follows from them.

## Evidence and next experiment

The checked repository Sage launcher produced [sage_runtime_info.json](sage_runtime_info.json) before the measured workers. Two initial child runs completed their arithmetic but their parent resource monitors failed on restricted macOS process APIs; [attempt1](attempt1/attempt.json) and [attempt2](attempt2/attempt.json) retain their outputs and failure statuses. Corrected parent monitors then completed N41, N131, and scaling runs, with all terminal receipts and raw stdout/stderr preserved. `python3 verify.py` returned `PASS_BLOCK_NORM_ARCHIVE`: it checks frozen source hashes, archived failed attempts, monitor caps and transcript hashes, N41 direct hits, N131 retained codes, and all scaling decisions against the independent reference. The reused `JointNorm` Lean theorem was rebuilt with its pinned toolchain; `#print axioms` reports only `propext` and `Quot.sound`.

The next algorithmic test should couple **at least three free pair families to the public target before specializing any two-pair residual**. It must measure retained family count and total residual-generation plus rejection cost on an unpinned N41 public query against the 38.246-second exact four-pair join, retain every one of its 32 independently replayed relations, and only then freeze an N131 ordinary-point relation run within the one-worker 600-second/4-GiB envelope. The present block norm is useful as an exact certificate and control, but its measured degree scaling makes it a poor inner search accelerator.
