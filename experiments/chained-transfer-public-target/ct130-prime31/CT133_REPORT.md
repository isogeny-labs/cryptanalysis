# CT133 — Native independently implemented cold CM-neighbor ECDLP screen

**2026-11-15 · producer-local, [pcc:unverified].** This is a concrete same-host **toy** prime-field, single-target, cold solve-cost comparison, **not** a complete, independently admitted ECDLP advantage or a generalized prime-field attack. Parent: cryptanalysis #1541; root: crypto #3877. Frozen protocol and the output-schema correction were committed in advance of the replacement four-panel holdout. The first four panels (20261201–04) are permanently **quarantined exploratory** because they recorded known scalars instead of independent recovered scalars. Both batches are preserved in the turn-local zip, not yet a signed GitHub PCC archive.

## Measured new holdout

C++17 -O3 on one local AMD EPYC 9V74 container (5 visible CPUs); one process per seed. Source E over p=2147483033, a=622683939, b=2147483024, j=287496; q=536857417 prime. Degree-2 isogeny to T:y²=x³+9x (j=1728). Three full cold *online* scalar recovery arms on exactly the same public G,Q: source fresh-table BSGS (width 23171), source negation-rho (fresh jumps), target fourfold-CM rho after **mapping both G and Q** (fresh jumps). Every trial computes/validates a real source scalar, not merely a group-operation proxy. Exactly 64 public targets per predeclared seed, 6 alternating ABCCBA/CBAABC solves/target, **256 targets / 1536 actual solves**. All 1536 recovered source public logarithms matched known-answer controls.

| Predeclared panel | Cold source BSGS, ns | Cold source neg-rho, ns | Cold target mapped GLV-rho, ns | Best tested source / target |
|---|---:|---:|---:|---:|
| 20261210 | 1,259,919,238 | 980,023,912 | 679,084,293 | 1.443155 |
| 20261211 | 1,229,413,217 | 976,365,010 | 702,847,836 | 1.389156 |
| 20261212 | 1,206,279,493 | 827,792,428 | 646,768,955 | 1.279889 |
| 20261213 | 1,260,872,684 | 859,618,054 | 652,129,797 | 1.318170 |
| **Pooled** | **4,956,484,632** | **3,643,799,404** | **2,680,830,881** | **1.359205** |

Within-panel A/A median max/min across duplicated arm observations: 1.0316, 1.0285, 1.0174 and 1.0322 respectively. Fixed-target paired bootstrap descriptive 95% range for the pooled ratio: **1.254–1.476**, *not* isolation-, host- or curve-population confidence. Peak whole-process RSS in the first four, exploratory-format panels was roughly 5.9–6.4 MiB; the final four .time records are in the archive. Memory is not arm separated. Source verification and target point map are *timed*, but curve-discovery/CM parameter setup are not. The cost field counters omit mapping inversions even though elapsed time includes them. The C++ legacy `cycles` column for BSGS is actually its 23171-entry table width; the independent audit enforces this explicitly. No best external native source-rho or cold IC was run.

## Evidence and controls

- New C++ code: `ct133_native.cpp`, SHA256 `ce654352cf364298f91b7417c02e5b329f0e05f291dd985794e7c06314474e6f`.
- Locally executed separate Python verifier: `ct133_validate.py`, SHA256 `326f49ef9734c04cb1f9a70fd4508e6fd11ab7992c9719c891c0d87dff72a9f8`. GitHub-submitted verifier follows the same arithmetic and mutation checks but its bytes must be confirmed independently by exact-head CI.
- Raw unfiltered panels SHA256, ascending seeds: `47ee7e2dc41a125cd13266074e8138dbde8f992dc1410fce791b5485cd38bed5`, `ba7c9a384d3abd5c600deb551ec9816d65b3578f424882ee579de9b25ae97c95`, `0fa020023a14d6a55e7c863316e27b5debf9bdb855c61be987752c53c7b9d20d`, `1dac826fb8114c2a689f9b7e2520e714410c0ab9fe38ed5088a1e24273e9283e`.
- Independent Python implementation re-derives source (j=287496), checks public source points, subgroup identity, isogeny images and target CM eigenvalue, parses all 1536 solver outputs, checks schedule and aggregate counters, and rejects **10 synthetic mutation types** in both `python3 -S` and `python3 -O -S`. Producer-local normal/-O audit JSON identical, sha256 `44f9b1aade7432b091a2340a02aa07875ab3db72f7b2f5f8020c4a7c68eb6d8e`.
- A narrow exact-PR-head CI workflow reruns all four frozen seeds, both Python modes, and stores raw receipts as an Actions artifact. **CI outcome is not asserted here until separately checked.** Local raw and negative controls are available from the conversation's downloadable evidence bundle, not GitHub-attested yet.

Reproduce on local free/authorized CPU:
```sh
cd experiments/chained-transfer-public-target/ct130-prime31
g++ -O3 -std=c++17 -Wall -Wextra -Wpedantic -o ct133_native ct133_native.cpp
for seed in 20261210 20261211 20261212 20261213; do ./ct133_native 64 "$seed" > "ct133_${seed}.csv"; done
python3 -S ct133_validate.py ct133_2026121{0,1,2,3}.csv --self-test
python3 -O -S ct133_validate.py ct133_2026121{0,1,2,3}.csv --self-test
```

## Why this is not yet the owner acceptance result

The advantage is **real measured wall-clock evidence for these exact two source implementations** on a deliberately CM-isogenous curve, not a new asymptotic algorithm. The strongest source may exploit additional endomorphisms or faster projective/Jacobian rho, and external IC has not been matched. It does not instantiate the frozen 695/701-record genus-2/3 Jacobian full-group correction, real native C169/C13a/C13b/D pricing or all transfer setup/linear algebra; curves of arbitrary j, including NIST prime curves, are outside the evidence. No independent PCC signature, stable isolated host or admitted full ECDLP advantage. No paid compute, EKS, benchmark promotion or protected merge.

**Technical next experiment:** matched strongest optimized source rho and source-side transported-endomorphism control on exactly these public panels; simultaneously execute the separate CT126 #1534 original-prime Jacobian primitive bench and full 701/695 parity via #1523/#3877. Drop or reprice the transfer if the stronger source wins.

**Prior art and concurrent work:** cryptanalysis #1539/#1540/#1541/#1534/#1523, crypto #3877/#4215/#4178 and CT35 cold-isogeny negative #1500; GLV (2001), Longa–Sica (2014), standard automorphism folding. Research-KB MCP/checkout wrapper and Conductor not accessible; no novelty or absence claim.
