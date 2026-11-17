# CT136 — matched batch32 affine inversion cold ECDLP comparator

2026-11-15. [pcc:unverified]. **Scope:** specially selected ordinary CM-neighbor curve over F_(2147483033), q=536857417. Research-only prospective protocol [CT136_PROTOCOL.md](CT136_PROTOCOL.md) was committed at **30b901da** before holdout execution. Parent source CT135 Git blob 4d94fc9163e86689a09c6d6685dd017c5c4c9698 remained unchanged. This is **not** a complete original-prime Jacobian ECDLP attack.

## Tested algorithm and model

On the identical public (G,Q) source point, five independently timed cold arms: fresh BSGS, source negation-fold affine rho, target fourfold affine rho including both 2-isogeny maps, source negation-fold **batch32** rho, target fourfold **batch32** rho including both maps. Each batch processes 32 independently initialized rho lanes, uses a Montgomery prefix-product inversion for up to 32 affine additions, and charges complete cold jump initialization, all lanes, collision table and original-source scalar verification. Both optimized source and target were allowed the same batching. Different derived group coefficients are checked at every collision. The preexisting CT135 affine routines are included unchanged using a renamed reference main; the new code is additive.

Every returned scalar must agree with the source public Q, its mapped target and the independently computed Python curve/isogeny identities. Separate Python reimplements **std::mt19937_64** to reconstruct each frozen public scalar from the seed, checks all ten rows per target, fresh-table widths and deterministic duplicate counters, aggregates, five arm labels, provenance and eleven sabotage mutations in both ordinary and optimized Python. **Code-path scalar-inversion count = 1 for a successful rho collision; that field is inferred, not a direct hardware counter.** Field inversions are instrumented from the common C++ inv() call, including the target map and postverification.

## Actual local prospective comparison

Protocol-frozen seed values 20261230–33, 64 distinct public targets each, ten complete solves each, AB(C)(D)(E)(E)(D)(C)(B)(A)/reverse alternating. **2,560 verified cold scalar recoveries.** Linux x86_64/AMD EPYC 9V74, Debian g++ 14.2, four cgroup CPUs, 5.8 GiB visible. `g++ -O3 -std=c++17 -Wall -Wextra -Werror`. Timing excludes externally supplied public-point creation and choice of special curve; includes each target's two mapping calls and original-source verification. Peak process RSS per panel 5,564–6,520 KiB; wall process time 1.89–2.00 s per 640-solve panel.

| Fixed seed | Best source batch32 (ms, sum 128 solves) | Best mapped target batch32 (ms, sum 128 solves) | Source / target |
|---|---:|---:|---:|
| 20261230 | 333.486 | 233.390 | 1.428881 |
| 20261231 | 325.626 | 258.823 | 1.258101 |
| 20261232 | 321.951 | 250.636 | 1.284537 |
| 20261233 | 313.373 | 256.360 | 1.222394 |
| **Total** | **1,294.436** | **999.209** | **1.295461** |

The source batch implementation wins over its source affine rho and BSGS comparators, and the target batch implementation wins over target affine rho, on every panel. Both optimized arms therefore provide a **more conservative and fairer comparison** than CT135's two original rho arms. Local descriptive fixed-cohort paired bootstrap interval: **[1.196, 1.398]**. This is a measured **scoped toy single-target DLP advantage**, not a rigorous population confidence interval, independent-host measurement, or accepted full-chain advantage.

Raw CSV SHA-256:
- 20261230 `f5e8a3777737dcdd8e3799fcd1256ba46352974f6a9e4009dc0bba9c7a911a15`
- 20261231 `b521941e88ae178ce6f88f4a3e44fb28dab727220ceb7c2382bf42399d7fc2bd`
- 20261232 `69457ba106a0a7e5c501bc79c516fa0be6b14ad6fc2a26d9d2d34a95e7e21913`
- 20261233 `51315f42e15fe21e2edc08ffeed83e90c6796d0aa6a038aab62b2aa9fa5ea80c`

Exact executed SHA-256: `ct136_native.cpp=20b0305d0b291602dd141a278c00459c47e78608f17e33bea6395a3106438921`; `ct136_verify.py=ce3a9e5af959ad5ec3a81ce78151587a099fa8f86029bc7fa059bf9a384abc2f`. Git blob SHA-1s: `2d063737bae8262ef39d9af4a9df8b022ef2da60` and `09077d603e6a05be373a5157eaaa19754bb934f9`; source SHA-256 stored in local evidence ZIP. No mutable benchmark admission or signed PCC promoted.

## Reproduction

```bash
cd experiments/chained-transfer-public-target/ct130-prime31
test "$(git hash-object ct135_native.cpp)" = 4d94fc9163e86689a09c6d6685dd017c5c4c9698
g++ -O3 -std=c++17 -Wall -Wextra -Werror ct136_native.cpp -o ct136_native
for seed in 20261230 20261231 20261232 20261233; do
  /usr/bin/time -f 'wall=%e maxrss_kb=%M' -o "$seed.time" ./ct136_native 64 "$seed" > "$seed.csv"
done
python3 -S ct136_verify.py 2026123{0,1,2,3}.csv > audit.json
python3 -O -S ct136_verify.py 2026123{0,1,2,3}.csv > audit-optimized.json
cmp audit.json audit-optimized.json
sha256sum 2026123*.csv ct136_native.cpp ct136_verify.py
```

Separate [CT136 scope-specific GitHub Actions](../../../.github/workflows/ct136-batch-rho-cold.yml) run on exact PR head, retain independently generated stdout/stderr, hashes and resource receipts for 30 days. Its result must be inspected after creation; **no prospective hosted CI or PCC outcome is asserted by this local report**.

## Scientific limits and next decision

The degree-two isogeny retains q exactly. A fourfold target orbit yields at best a **constant-factor generic-rho improvement**, not a new subexponential ECDLP algorithm. The source is a specially chosen CM-neighbor; the isogeny-search/construction cost and faster source endomorphism/projection methods are **not charged**. CT136 is stronger than CT135's original affine comparison but still lacks strongest projective/batched source and independently matched index calculus from crypto #4178; most importantly it is **not** the 695/701 original-prime Jacobian chain. Native C169, C13a, C13b and D, correction/halving classes, complete original-prime cold setup+LA+memory and signed PCC remain outstanding in #1534/#1523 and crypto #3877. Without those, there is **no accepted complete ECDLP advantage**. No paid compute, EKS/Spot job, protected merge or PCC signing.

**Next:** independently hosted exact-code CT136 replay with A/A; then original-prime #1534 native primitive pricing/full cold references, or strongest projective source rho if it challenges the CM toy. A slower outcome gets recorded and shifted to the next expected-value index-calculus lead. Related: cryptanalysis #1546 (CT135), #1545 (CM source control); crypto #4215/#3877; GPU IC #4178's S remains much greater than rho.


## Independently hosted exact-head reproduction — 2026-11-15 13:09 UTC [pcc:unverified]

[GitHub Actions run #43717455264](https://github.com/isogeny-labs/cryptanalysis/actions/runs/43717455264), job **132821955085**, completed **success** on exact PR source/report head `ff498825bba6c6ff1f00638388c1b418e925d38d` (not a synthetic merge). The complete 360-line decoded job log was inspected: fixed CT135 blob guard, C++17 compilation, four preregistered 64-target panels, two byte-identical independent Python arithmetic audits (normal and optimized), **2,560** correct complete cold DLP recoveries, and **11/11** corrupted-record rejections. Exact hosted transcript is not interchangeable with producer-local raw timings.

| Hosted prospective panel | Source batch32 total ns | Target batch32 total ns | ratio |
|---|---:|---:|---:|
| 20261230 | 225396314 | 165128549 | 1.364975 |
| 20261231 | 202738964 | 170548841 | 1.188744 |
| 20261232 | 216651790 | 177080495 | 1.223465 |
| 20261233 | 200465358 | 169592161 | 1.182044 |
| **Pooled** | **845252426** | **682350046** | **1.238737** |

Hosted fixed-cohort descriptive bootstrap [1.151869,1.331273]. All panels favor mapped batch32 rho relative to the **best of the three tested source arms**; this is scoped constant-factor evidence, not original-prime full-Jacobian owner acceptance. The [13-file GitHub artifact #14162348665](https://github.com/isogeny-labs/cryptanalysis/actions/runs/43717455264/artifacts/14162348665) retains independently generated CSVs, both audit modes, code hashes, host and RSS/time receipts (30-day retention). Uploaded artifact SHA256 `d88f48e2440cb27a9442ba6a8ae71cd7783f96036d74d51e6b10e07445b0e6e6`. GitHub runner Ubuntu 24.04/g++ environment was independent of producer-local Debian 14.2. Signed PCC, complete strongest source rho/IC, actual CT126 original-prime C169/C13a/C13b/D and full Jacobian cold solves remain unverified. [pcc:unverified].
