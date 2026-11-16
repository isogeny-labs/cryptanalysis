# CT154 — source ECDLP with genuinely public-point input; mixed negation-rho negative result

16 November 2026 UTC. Root [crypto #3877](https://github.com/isogeny-labs/crypto/pull/3877), stacked [cryptanalysis #1589](https://github.com/isogeny-labs/cryptanalysis/pull/1589). Standing: **[pcc:unverified]**. [Prospective protocol](CT154_PUBLIC_INPUT_RHO_PROTOCOL.md) committed at `80d882f6` and corrected for alternating block order at `297b140f` **before** full paired measurements. Early local non-timed development failed with short negation-map fruitless cycles; that failure is preserved rather than silently removed.

## Implementation and exact source

- Original CT152/153 source **E(F223^3)**: `F223[z]/(z^3-3)`, `a2=(127,56,199)`, `a4=(152,35,36)`, `a6=(212,109,150)`, `G=((162,197,140),(45,11,207))`, prime subgroup `ell=2773073` and full order `4ell=11092292`. The distinct nu12 model is not used.
- `ct154_public_point_reference.cpp` includes unchanged `ct153_original_cold_reference.cpp` for the original C++ group law, cold BSGS and ordinary three-way rho. The CLI accepts **six public Q coordinate limbs only** (no known scalar), checks on-curve and subgroup membership, and independently verifies each recovered scalar by `[k]G=Q`.
- Added a 16-partition deterministic mixed r-adding walk on `E/{±1}`: canonical sign selection adjusts both `a,b` mod ell; restart tables are deterministically keyed to the restart index, not the fixture scalar. A same-partition re-entry escape performs doubling to avoid common exact-state length-two fruitless loops; every returned log is group-verified. Hard bound: 40 restarts × 20,000 Floyd iterations. This is not claimed to be the strongest optimized rho.
- Independent `ct154_public_input_audit.py` constructs public targets using separate Python finite-field/elliptic arithmetic from CT153, passes coordinates without the scalar to C++, then verifies every recovered log and all output metadata. Eight malformed/incorrect-input controls require rejection; six 50-step negation-walk invariant checks and six full-solve self-checks run inside the C++ self-test.

**Git blob equality before publication:** local built C++ file `f8675a82a1e1b48f742c15fa61a732f0e9a9eaf2`, independent auditor `ebbf1059afedc2ca76a0c375d0858a3c08b196cc`, reused CT153 C++ `d814a99e9d98b66d37ba1ceeefbd4e819d7b68a8`; each matched the corresponding exact GitHub blob SHA-1 returned from the stacked branch.

## Completed developer-host paired diagnostic — **source only**

`Linux-6.18.57-x86_64-with-glibc2.41`, g++ C++17 `-O3 -Wall -Wextra -Werror`, non-isolated CPU. Six frozen known-answer public Q values generated *outside* C++; two alternating ABCCBA/CBAABC blocks per Q, each executable invocation a fresh process: **72/72 complete source answers**, 24 per arm, externally checked by independent Python. Eight wrong-input controls rejected. No EKS Spot, GPU or paid compute.

| Diagnostic | Fresh-table BSGS | Three-way ordinary rho | Mixed negation-rho |
|---|---:|---:|---:|
| Median spawn-inclusive wall (ms) | **3.504** | 5.596 | 8.264 |
| Median solver duration (ms) | **0.744** | 2.675 | 5.403 |
| Median field inversions | **1,804.5** | 6,389.5 | 13,517.5 |
| Peak child VmHWM (KiB) | 1,792 | 1,708 | 1,708 |
| Max rho restarts among all samples | N/A | 0 | 7 |

- Over 12 alternating paired blocks, median BSGS-minus-ordinary-rho spawn-wall delta **−2.099 ms**; 4,000-sample seeded fixed-case block-bootstrap95 **[−3.190, −0.281] ms**.
- BSGS-minus-mixed-neg-rho median **−4.990 ms**; fixed-case bootstrap95 **[−7.149, −2.414] ms**.
- Within-arm A/A median absolute spawn-wall drift **0.766 ms**.
- Raw 72-row canonical JSON row digest `9f77b8d01cfd7a6c43e863889f2bae052f89ca480281fe6bcc6ecb3e44acb196`; full local JSON file SHA256 `bd815cf30e13361cd48c09f4cb162a1e834dad5d154c67d800cd73be2690d65c`. C++ binary SHA256 `004b48385d418c97d55d381faa42519cebde8f96be9bc3c553015ac92453a328`. **Raw local file is not yet in GitHub or signed PCC**; the raw diagnostic is available as a conversation attachment and reproducible using commands below.

**Negative outcome:** this particular mixed negation-rho is slower than both fresh BSGS and the ordinary rho on these fixed 22-bit source tests. Do not treat the above bootstrap as a population confidence interval or proof of best available generic solver. The initial unescaped negation candidate exhausted 40 restarts in fruitless cycles for `Q=G`; the escape fixed correctness on the six selected cases, but did **not** improve observed end-to-end source-solve cost. **[pcc:unverified]**.

## Reproduction and remaining gates

```sh
D=experiments/chained-transfer-public-target/norm-point-reuse-01
g++ -std=c++17 -O3 -Wall -Wextra -Werror "$D/ct154_public_point_reference.cpp" -o /tmp/ct154
/tmp/ct154 --self-test
python3 "$D/ct154_public_input_audit.py" /tmp/ct154 --quick
python3 "$D/ct154_public_input_audit.py" /tmp/ct154 --output /tmp/ct154-72-raw.json
```

Source-only workflow `.github/workflows/ct154-public-point-neg-rho.yml` runs bounded quick arithmetic and negative checks; it must be inspected on exact head before claiming hosted replay. Hosted CI, local Python cross-check, hash agreement and a producer's `verified:true` JSON field do **not** substitute for independent signed PCC.

Sources checked: AGENTS, today's session log, crypto #3877/#4215/#4178, cryptanalysis #1523/#1533/#1562/#1589 and CT153, Edlyn Teske's *On Random Walks for Pollard's Rho Method* (Math. Comp. 2001), and Bos–Kleinjung–Lenstra *On the Use of the Negation Map in the Pollard Rho Method* (ANTS 2010; [EPFL source](https://infoscience.epfl.ch/entities/publication/78564706-286d-4c6a-8a13-25c5d38fe72c)). Shared research-KB MCP absent in this runtime; neither novelty nor a rigorous prior-art absence is asserted.

**Next strongest unblocked work:** independently verify the producer-reported native full-695 original/optimized norm-point reuse corpus using original `check_final` and all exceptional/negative rows, then owner-admitted C169/C13a/C13b/D and complete *transferred* cold target DLP versus strongest same-host rho/BSGS/IC (full setup, correction, isogeny/Weil lift, Jacobian arithmetic, linear algebra, memory, verification, uncertainty and signed PCC). **None** of those latter measurements were made by CT154. The CT151/152 Frobenius obstruction still prevents interpreting this cubic-source model as an arbitrary prime-field ECDLP transfer.
