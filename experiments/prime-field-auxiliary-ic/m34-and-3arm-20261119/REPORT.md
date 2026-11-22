# Prime-Field Auxiliary IC: Preregistered 5-Encoding / 3-Arm Panel, $m=3,4$ Split-$S_3$ Circuits, and `#1347` / `CT186` Audits

## Executive Summary

This experiment executes Workstream 4 of the prime-field ECDLP and auxiliary-curve investigation in `crates/prime-field-auxiliary-ic` and `ca-ic auxiliary` [pcc:unverified]:

1. **Lead P0-2a (Preregistered 5-Encoding / 3-Arm Random-vs-Special Panel)**: Before running any solver, `protocol_and_targets.json` (`sha256 = 5aa4f11447fd3f9a94142c4cf0fb1e2591f4ccb2a853d6539d1efc2a9f6d448d`) froze three random-base seeds (`701, 702, 703`), five fresh hash-to-curve targets `E1_T0..E1_T4` on $E_1 / \mathbb{F}_{2^{31}-1}: y^2 = x^3 + 2x + 14$ ($n_1 = 2147505293$), two fresh targets `E2_T0..E2_T1` on $E_2 / \mathbb{F}_{2^{31}-1}: y^2 = x^3 + 2x + 36$ ($n_2 = 2147506201$), and a cofactor-subgroup check `E61_T0` on $E_{61} / \mathbb{F}_{2^{61}-1}: y^2 = x^3 + 3$ ($n = 157632877033$, cofactor $14627932$) [pcc:unverified]. Across all 17 `compare_reports.py` checks (`status = "aligned"`) and 49 independent certificate replays (`0` false relations, exact scalar agreement with C batched Montgomery `--rho`), relation yield is conserved at equal folded column count $K$ (`KN-FIND-007` confirmed: `3.348e-6` vs `3.122e-6` relations/query across the 5 full solves on $E_1$, bracketing $K^2 / ((n_1 - 1)/2) = 3.133 \times 10^{-6}$), while every IC arm remains $> 10^4\times$ slower than C batched Montgomery `--rho` (`mean 1.49 ms` vs `15.6–28.1 s`) [pcc:unverified].
2. **Lead P0-2b (Division-Free $m = 3$ and $m = 4$ Split-$S_3$ Resultant Circuits + Sparse mod-$n$ Solver)**: `crates/prime-field-auxiliary-ic` and `ca-ic auxiliary --summands 2|3|4` now support exact division-free $m = 3$ and $m = 4$ signed decompositions over `Auxiliary`, `Multiplicative`, `Torus`, and `Direct` factor bases, paired with incremental sparse mod-$n$ Gaussian elimination (`SparseSystem`) and independent `MultiCertificate` replay (`verify_multi_certificate`, single interleaved Jacobian multi-comb without field inversions) [pcc:unverified]. Exhaustive oracle tests over all curve points on $p = 31$ (with 2-torsion) and $p = 127$ pass with zero discrepancies, and full 31-bit solves on `E1_T0` confirm massive walk-query compression (`10,968,302` at $m = 2 \to$ `469,654` at $m = 3 \to$ `13,971` at $m = 4$ on `Arm A`/`Arm B`, a `785.1x` walk reduction) [pcc:unverified]. On Apple Silicon (`aarch64`, scalar 4-wide ILP backend without `x86_64` AVX2/AVX-512 IFMA), the 3-step `Multiplicative(126)` resultant circuit (`Cube + Cube + Septic`) beats same-base direct subtraction at $m = 3$ (`22.169 s` vs `29.172 s`, `1.316x` faster) and $m = 4$ (`43.640 s` vs `53.495 s`, `1.226x` faster), and $m = 3$ (`22.169 s`) reduces end-to-end 31-bit solve wall time below $m = 2$ (`37.258 s` circuit / `31.788 s` direct) while still trailing C `--rho` (`2.12 ms`) by four orders of magnitude [pcc:unverified].
3. **Leads P1-3b & P1-4b (Disjoint 3-Window `#1347` $\mathbb{F}_p$ CDCL(T) Audit + `CT186` Prime-Field Cost Floor)**: Native Rust audits (`examples/cdclt_ct186_audit.rs` and `tests/cdclt_ct186_audit.rs`) reproduce exact `#1347` `development_oracle.cpp` counts on $E/\mathbb{F}_7$, prove zero unit propagations prior to $(k - 1)s = 2s$ assigned window bits under live explanation-tracked $\mathbb{F}_p$-RREF, and measure exact 2-watched-literal + 1-UIP conflict scaling `theory_conflicts = 2^{2s}` (`slope e = 2.000000` on exhaustive UNSAT $s = 5..8$, `slope e = 1.993111` on planted SAT $s = 5..10$, failing the `e < 0.5` gate) with `min_raw_nogood_width = 2s` [pcc:unverified]. Combining the `CT198` route-delta cancellation `(C13a + N2 + C13b) - (C169 + N2) == C13a + C13b - C169` with `CT143`/`CT186` genus-2/3 destination index calculus (`GTTD07` / Diem DLP) places the prime-field Jacobian-transfer floor at $\widetilde{\Omega}(p) \gg \Theta(p^{1/2})$, i.e., `32.0, 62.0, 129.0, 257.0` $\log_2$ ops versus Pollard $\rho$'s `15.33, 30.33, 63.83, 127.83` at `31, 61, 128, 256` bits [pcc:unverified].

---

## Provenance & Receipt Inventory

- **Source commit**: `6805d56f490423cc7cb7c17b9ddb3fb95f16674c` (`ca-ic` release binary `blake3 = 1e52662e681ba7aeacc4c3339fe3764f3f8e5b2b038f0dd720f9b6620305df06`) [pcc:unverified].
- **Host architecture**: macOS `darwin 27.2.0` (`aarch64`), `Backend::Auto -> Backend::Scalar` (4-wide ILP scalar circuit; `AVX2` and `AVX-512 IFMA` paths in `circuit_x86.rs` apply to `x86_64` hosts) [pcc:unverified].
- **Artifacts in `experiments/prime-field-auxiliary-ic/m34-and-3arm-20261119/`**:
  - `protocol_and_targets.json` (`sha256 = 5aa4f11447fd3f9a94142c4cf0fb1e2591f4ccb2a853d6539d1efc2a9f6d448d`): frozen seeds and hash-to-curve public targets derived without planted scalars [pcc:unverified].
  - `yield_panel_summary.json`: 5-target $\times$ 11-run `524,288`-query yield panel on $E_1$, 2-target panel on $E_2$, 61-bit cofactor refusal + cleared `Arm C` check, 17/17 `compare_reports.py` alignments, and matched $m = 2, 3, 4$ prefix runs [pcc:unverified].
  - `end_to_end_solves_summary.json`: full certificate-verified 31-bit solves across all 5 $E_1$ targets, $E_2$, and $m = 3, 4$ on `E1_T0`, plus C `--rho` baselines and CLI `--replay-relations` checks (`49` independent replays, `0` false relations) [pcc:unverified].
  - `cdclt_and_ct186_audit.json`: deterministic output of `cargo run --release --manifest-path crates/prime-field-auxiliary-ic/Cargo.toml --example cdclt_ct186_audit` [pcc:unverified].
  - `run_panel.py`: deterministic driver reproducing `protocol_and_targets.json`, `yield_panel_summary.json`, and `end_to_end_solves_summary.json` [pcc:unverified].

---

## Lead P0-2a: Preregistered 5-Encoding / 3-Arm Panel (`KN-FIND-007` & Circuit vs Direct Controls)

### 1. Aligned `524,288`-Query Prefix Panel on $E_1(\mathbb{F}_{2^{31}-1})$ ($n_1 = 2147505293$)

All arms share `search_seed = 20261119` and `walk_lanes = 64` (`2,621,440` total queries per arm summed over `E1_T0..E1_T4`) [pcc:unverified]. Every `compare_reports.py` triplet (`Arm A` vs `Arm B` vs `Arm C` across 5 $E_1$ targets $\times$ 3 random seeds + 2 $E_2$ targets = 17 triplets) returned `status = "aligned"` [pcc:unverified].

| Arm | Encoding / Control | Raw Fiber | Folded $K$ | `columns_blake3` (prefix) | Relations (`T0..T4`) | Total Rels | Mean Decomp (`ms`) | Uses Circuit |
| --- | --- | ---: | ---: | --- | --- | ---: | ---: | :---: |
| `Arm A` | `Auxiliary` (2-map union, 6 `Rational` steps) | 128 | 58 | `1f266e67fed4...` | `[2, 0, 1, 2, 3]` | 8 | 1157.45 | yes |
| `Arm B` | `--without-auxiliary` (same `Arm A` columns) | 128 | 58 | `1f266e67fed4...` | `[2, 0, 1, 2, 3]` | 8 | 663.94 | no |
| `Arm C (701)` | `--random-base-columns 58` (`seed = 701`) | 58 | 58 | `66fad47708b0...` | `[0, 1, 2, 1, 0]` | 4 | 654.20 | no |
| `Arm C (702)` | `--random-base-columns 58` (`seed = 702`) | 58 | 58 | `df5a2ac5400d...` | `[2, 0, 0, 0, 1]` | 3 | 621.77 | no |
| `Arm C (703)` | `--random-base-columns 58` (`seed = 703`) | 58 | 58 | `77eaccec8b95...` | `[2, 3, 2, 3, 1]` | 11 | 625.33 | no |
| `Arm D` | `--multiplicative-degree 126` (`Cube^2 + Septic`) | 126 | 56 | `32b169d60308...` | `[1, 2, 2, 1, 2]` | 8 | 594.80 | yes |
| `Arm D ctrl` | `--multiplicative-degree 126 --without-auxiliary` | 126 | 56 | `32b169d60308...` | `[1, 2, 2, 1, 2]` | 8 | 642.17 | no |
| `Arm D rand` | `--random-base-columns 56` (`seed = 701`) | 56 | 56 | `a2d7cbfc6f2c...` | `[0, 1, 1, 1, 0]` | 3 | 642.94 | no |
| `Arm E` | `--torus-depth 7` (6 `TorusSquare` steps) | 128 | 71 | `003eb1e8be48...` | `[3, 0, 1, 1, 2]` | 7 | 1339.61 | yes |
| `Arm E ctrl` | `--torus-depth 7 --without-auxiliary` | 128 | 71 | `003eb1e8be48...` | `[3, 0, 1, 1, 2]` | 7 | 837.53 | no |
| `Arm E rand` | `--random-base-columns 71` (`seed = 701`) | 71 | 71 | `23a5a5552ad3...` | `[0, 2, 2, 3, 1]` | 8 | 825.95 | no |

Secondary curve $E_2 / \mathbb{F}_{2^{31}-1}$ ($y^2 = x^3 + 2x + 36$, $n_2 = 2147506201$, $K = 68$) reproduced exact `Arm A == Arm B` relation parity (`[1, 2]` on `E2_T0, E2_T1`) and identical `Arm C (seed = 701)` yield (`[1, 2]`) [pcc:unverified]. On the 61-bit cofactor curve $E_{61} / \mathbb{F}_{2^{61}-1}$ ($n = 157632877033$, cofactor $14627932$), un-cleared fiber lifts were deterministically refused (`factor-base point is outside the target subgroup`), whereas cofactor-cleared `--random-base-columns 64` (`draws = 114`, `non_lifts = 50`, `cleared_to_identity = 0`) ran cleanly (`18.24 ms` for `8,192` queries) [pcc:unverified].

### 2. Full End-to-End $m = 2$ Certificate-Verified Solves on $E_1$ and $E_2$ vs C `--rho`

Every solve below passed independent certificate verification (`verify_certificate`, `[k]P == Q`, `0` false relations) and matched C batched Montgomery `--rho` [pcc:unverified].

| Target | Recovered $k \bmod n$ | `Arm A` Queries (`online_s`) | `Arm B` Same-Base (`online_s`) | `Arm C (701)` Queries (`online_s`) | `Arm D` Mul-126 Circuit (`online_s`) | `Arm D` Direct (`online_s`) | `Arm E` Torus-7 Circuit (`online_s`) | `Arm E` Direct (`online_s`) | C `--rho` Ops (`online_ms`) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `E1_T0` | `1201831812` | `10,968,302` (`22.66s`) | `10,968,302` (`13.67s`) | `10,644,671` (`13.70s`) | `16,557,569` (`37.26s`) | `16,557,569` (`31.79s`) | `10,607,350` (`26.52s`) | `10,607,350` (`20.09s`) | `83,997` (`4.60ms`) |
| `E1_T1` | `365764040` | `7,400,678` (`21.69s`) | `7,400,678` (`12.09s`) | `12,591,159` (`19.17s`) | `11,331,636` (`15.78s`) | `11,331,636` (`16.40s`) | `12,405,520` (`40.71s`) | `12,405,520` (`25.02s`) | `23,572` (`0.51ms`) |
| `E1_T2` | `1597547216` | `8,088,136` (`18.36s`) | `8,088,136` (`13.50s`) | `12,859,138` (`19.71s`) | `8,832,857` (`11.37s`) | `8,832,857` (`12.69s`) | `9,983,112` (`26.88s`) | `9,983,112` (`16.04s`) | `18,652` (`0.43ms`) |
| `E1_T3` | `194232092` | `12,473,685` (`25.03s`) | `12,473,685` (`18.66s`) | `13,179,156` (`18.43s`) | `13,195,565` (`14.71s`) | `13,195,565` (`15.50s`) | `11,349,291` (`27.11s`) | `11,349,291` (`18.01s`) | `31,487` (`0.89ms`) |
| `E1_T4` | `1538787206` | `13,036,520` (`26.40s`) | `13,036,520` (`20.25s`) | `9,975,418` (`14.44s`) | `12,494,706` (`15.14s`) | `12,494,706` (`16.70s`) | `7,432,187` (`19.13s`) | `7,432,187` (`12.28s`) | `48,482` (`1.04ms`) |
| **Mean (`E1`)** | — | **`10,393,464` (`22.83s`)** | **`10,393,464` (`15.63s`)** | **`11,849,908` (`17.09s`)** | **`12,482,467` (`18.85s`)** | **`12,482,467` (`18.62s`)** | **`10,355,492` (`28.07s`)** | **`10,355,492` (`18.29s`)** | **`41,238` (`1.49ms`)** |
| `E2_T0` | `1667675311` | `6,076,282` (`13.76s`) | `6,076,282` (`9.01s`) | `10,948,723` (`16.43s`) | — | — | — | — | `17,465` (`0.41ms`) |

**Key quantitative takeaways (`P0-2a`)**:
1. **`KN-FIND-007` relation-yield conservation holds**: Across the five full $E_1$ solves at $K = 58$, `Arm A` collected `174` relations over `51,967,321` queries (`3.348e-6` relations/query) and `Arm C (seed = 701)` collected `185` relations over `59,249,542` queries (`3.122e-6` relations/query), both matching the uniform signed-pair birthday density $K^2 / ((n_1 - 1)/2) = 58^2 / 1073752646 = 3.133 \times 10^{-6}$ within sampling variance (`Arm C` seeds `701, 702, 703` on `E1_T0` solved in `10.64M, 9.59M, 6.41M` queries, mean `8.88M` vs `Arm A`'s `10.97M`) [pcc:unverified]. Auxiliary-curve fibers confer **no smooth/algebraic relation-density boost** over an equal-$K$ random subgroup base [pcc:unverified].
2. **Scalar `aarch64` circuit step-depth threshold**: Every circuit arm produces bit-for-bit identical queries, relations, ranks, and proof DAGs as its `--without-auxiliary` same-base control [pcc:unverified]. On Apple Silicon (`Backend::Scalar`, 4-wide ILP without `x86_64` AVX2/AVX-512 IFMA), `Multiplicative(126)` (`first_pole = 0` plus 3 resultant steps: `Cube, Cube, Septic`) beats same-base batched Montgomery subtraction on 4 of 5 $E_1$ solves (`57.00 s` vs `61.29 s` across `E1_T1..E1_T4`, `1.075x` faster; `594.8 ms` vs `642.2 ms` mean prefix decomposition), whereas 6-step quadratic fibers (`Auxiliary` and `Torus` depth 7) take `1.46x` and `1.54x` longer than scalar Montgomery batched subtraction without `x86_64` SIMD [pcc:unverified].
3. **Cold setup + online wall vs `--rho`**: Factor-base preparation (`prep_ms`) is `0.12–1.01 ms` across all arms, while online decomposition dominates `> 98%` of IC wall time (`11.37–40.71 s`), trailing C batched Montgomery `--rho` (`0.41–4.60 ms`) by `~10,000x` [pcc:unverified].

---

## Lead P0-2b: Division-Free $m = 3$ and $m = 4$ Split-$S_3$ Circuits & Sparse mod-$n$ Solver

### 1. Algebraic & Implementation Design

- **$m = 3$ outer-shift resultant evaluation**: Given query $R$ and signed base points $\pm P_{i_1}$ ($2K$ outer shifts amortized via one shared Montgomery `batch_add_inner` inversion), each non-identity residual $R' = R - s_1 P_{i_1}$ pushes its shifted $S_3(x(R'), \cdot)$ quadratic through `zero_indices_from(..., i_1)` (restricting inner tiles to `i_2 >= i_1` in `AVX-512` / `AVX2` / 4-wide scalar tiles) to isolate $s_2 P_{i_2} + s_3 P_{i_3} = R'$ with zero field divisions inside the inner loop [pcc:unverified]. The boundary case $R' = \mathcal{O}$ (`R = s_1 P_{i_1}`) emits canonical 3-term relations via $P_{i_1} + P_{i_2} - P_{i_2} = R$ or curve 2-torsion when present [pcc:unverified].
- **$m = 4$ chunked outer-pair shifts + split-$S_3$ circuit**: Outer signed pairs $s_1 P_{i_1} + s_2 P_{i_2}$ (`i_1 <= i_2`) are formed in 256-pair chunks (`batch_add_inner`), shifted against $R$, and fed into `zero_indices_from(..., i_2)` for `i_2 <= i_3 <= i_4`, supplemented by the exact 3-cycle-to-$\mathcal{O}$ branch when $R = \pm P_m$ ($s_a P_a + s_b P_b + s_c P_c = \mathcal{O}$ via `find_pair_from`) [pcc:unverified].
- **Exact sparse mod-$n$ elimination & certificate replay**: `SparseSystem` maintains incremental prime-modulus RREF over merged signed rows $\sum_t c_t x_t \equiv a + b k \pmod{n}$ (`|c_t| <= 4`) using the existing bounded `Proof` combination DAG, and `Curve::matches_multi_linear_combination` verifies each `2..=4`-summand relation in a single interleaved Jacobian scalar loop with zero inversions [pcc:unverified].
- **Exhaustive small-prime oracle parity (`tests/multi_summands.rs`)**: Across every rational point on $E/\mathbb{F}_{31}: y^2 = x^3 + x + 3$ (even order `36` with 2-torsion) and $E/\mathbb{F}_{127}: y^2 = x^3 + 2x + 5$ (prime order `127`) over `Auxiliary`, `Multiplicative`, `Torus`, and `Direct` bases, `FactorBase::decompose_multi` at $m = 2, 3, 4$ matches brute-force tuple enumeration (`100%` canonical row-set equality) [pcc:unverified].

### 2. End-to-End 31-Bit $m = 2, 3, 4$ Benchmark on Fresh Target `E1_T0` ($k = 1201831812$)

All runs below solved `E1_T0` on $E_1(\mathbb{F}_{2^{31}-1})$ from scratch (`search_seed = 20261119`), verified every relation and linear proof step via `verify_multi_certificate` AND CLI `--replay-relations` (`0` false relations), and matched `--rho` (`scalar = 1201831812`, `83,997` group ops, `2.12–4.60 ms`) [pcc:unverified].

| Summands $m$ | Arm | Folded $K$ | Walk Queries | Query Compression vs $m=2$ | Relations (Rank) | Proof Nodes | Decomp (`s`) | Total Online (`s`) | Circuit vs Direct Speedup |
| :---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `2` | `Arm A` (`Auxiliary` circuit) | 58 | `10,968,302` | `1.00x` | `40 (39)` | 95 | 22.283 | 22.655 | `0.603x` |
| `2` | `Arm B` (`--without-auxiliary`) | 58 | `10,968,302` | `1.00x` | `40 (39)` | 95 | 13.295 | 13.667 | (control) |
| `2` | `Arm C` (`random_seed = 701`) | 58 | `10,644,671` | `1.00x` | `30 (29)` | 70 | 13.325 | 13.698 | — |
| `2` | `Arm D` (`Mul-126` circuit) | 56 | `16,557,569` | `1.00x` | `38 (37)` | 94 | 36.090 | 37.258 | `0.853x` (`1.075x` on `T1..T4`) |
| `2` | `Arm D` (`Mul-126` direct) | 56 | `16,557,569` | `1.00x` | `38 (37)` | 94 | 30.840 | 31.788 | (control) |
| `3` | `Arm A` (`Auxiliary` circuit) | 58 | `469,654` | **`23.35x`** | `56 (55)` | 263 | 58.476 | 58.500 | `0.676x` |
| `3` | `Arm B` (`--without-auxiliary`) | 58 | `469,654` | **`23.35x`** | `56 (55)` | 263 | 39.495 | 39.520 | (control) |
| `3` | `Arm C` (`random_seed = 701`) | 58 | `462,829` | **`23.00x`** | `56 (55)` | 275 | 34.248 | 34.267 | — |
| `3` | `Arm D` (`Mul-126` circuit) | 56 | `366,612` | **`45.16x`** | `45 (44)` | 148 | 22.153 | **22.169** | **`1.316x`** |
| `3` | `Arm D` (`Mul-126` direct) | 56 | `366,612` | **`45.16x`** | `45 (44)` | 148 | 29.155 | 29.172 | (control) |
| `4` | `Arm A` (`Auxiliary` circuit) | 58 | `13,971` | **`785.08x`** | `56 (55)` | 462 | 68.331 | 68.334 | `0.679x` |
| `4` | `Arm B` (`--without-auxiliary`) | 58 | `13,971` | **`785.08x`** | `56 (55)` | 462 | 46.368 | 46.371 | (control) |
| `4` | `Arm D` (`Mul-126` circuit) | 56 | `18,593` | **`890.53x`** | `56 (55)` | 607 | 43.637 | 43.640 | **`1.226x`** |
| `4` | `Arm D` (`Mul-126` direct) | 56 | `18,593` | **`890.53x`** | `56 (55)` | 607 | 53.490 | 53.495 | (control) |

**Key quantitative takeaways (`P0-2b`)**:
1. **Walk-query scaling matches combinatorial $m$-summand density**: Increasing $m = 2 \to 3 \to 4$ compresses target walk queries by `23.35x` ($m=3$) and `785.08x` ($m=4$) at $K = 58$, and by `45.16x` ($m=3$) and `890.53x` ($m=4$) at $K = 56$, because signed $m$-subsets grow as $\approx 2^{m-1} \binom{K}{m}$ while `i_1 <= i_2 <= ... <= i_m` tile pruning halves/sixths inner evaluations [pcc:unverified].
2. **`KN-FIND-007` persists at $m = 3$**: At $m = 3$, `Arm A` (`469,654` queries) and `Arm C (seed = 701)` (`462,829` queries) require virtually identical query counts (`1.015x`), confirming that special auxiliary fibers do not alter higher-arity $S_3$-chain relation probability either [pcc:unverified].
3. **Genuine circuit speedup on `Multiplicative(126)` at $m = 3, 4$**: Because `Multiplicative(126)` evaluates only 3 homogeneous resultant steps (`Cube, Cube, Septic`) over L1-resident column tiles without constructing sorted difference tables, `arm_D_mul126_circuit` beats `arm_D_mul126_direct` by **`1.316x`** at $m = 3$ (`22.169 s` vs `29.172 s`, and `954.51 ms` vs `1226.71 ms` on the `16,384`-query prefix) and **`1.226x`** at $m = 4$ (`43.640 s` vs `53.495 s`), making $m = 3$ faster end-to-end than $m = 2$ on `Arm D` while still $O(p / K)$ overall vs $\Theta(p^{1/2})$ Pollard $\rho$ [pcc:unverified].

---

## Leads P1-3b & P1-4b: Disjoint 3-Window `#1347` $\mathbb{F}_p$ CDCL(T) Audit + `CT186` Cost Floor

### 1. Native `#1347` Disjoint 3-Window CDCL(T) Nogood-Width & Scaling Audit (`s = 5..10`)

Inspecting commit `b1b4dcdf05` (`#1347`: `development_oracle.cpp`, `prime_field_cdclt.cpp`, and `experiments/prime-field-cdclt/REPORT.md`) alongside `/Volumes/SSD990-2/prime-fp-propagator-20261118/REPORT.md`, we audited the 3-summand split-$S_3$ system
$$S_3(x_2, x_R, u) = 0, \qquad S_3(x_0, x_1, u) = 0, \qquad (2 t \lambda - s_0)^2 = x_0^3 + a x_0 + b$$
over $E_1(\mathbb{F}_{2^{31}-1}): y^2 = x^3 + 2x + 14$ with disjoint $s$-bit window selectors $W_0, W_1, W_2$ ($|W_u| = 2^s$) in `examples/cdclt_ct186_audit.rs` [pcc:unverified]:

1. **Exact `#1347` $\mathbb{F}_7$ oracle parity**: On $E/\mathbb{F}_7: y^2 = x^3 + 3$ (order 13, windows `[3, 2, 2]`), our Rust audit reproduces `96` $\mathbb{F}_{p^2}$ candidates, `5` projected rational models, `294` $(2t\lambda - s_0)^2 = f(x)$ checks, and `49` $t = 0$ exceptional checks [pcc:unverified].
2. **Live $\mathbb{F}_p$-RREF bilinear-column rank barrier**: Because $2^s \ll p$ and every monomial $x_0^i x_1^j u^\ell$ ($0 \le i, j, \ell \le 2$) couples unassigned window bits across two variables, live explanation-tracked $\mathbb{F}_p$-RREF derives **0 unit propagations** whenever fewer than two windows ($2s$ bits) are fixed [pcc:unverified].
3. **2-Watched-Literal + 1-UIP CDCL(T) conflict scaling (`s = 5..10`)**:

| Instance Family | Window Bits $s$ | Order | SAT? | Theory Conflicts | Theory Propagations | Min Raw Nogood Width | Max Raw / 1-UIP Width | Mean 1-UIP Width | Fitted $\log_2$ Conflict Slope $e$ |
| --- | :---: | --- | :---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Exhaustive UNSAT | `5` | `window_major` / `bit_interleaved` | no | `1,024` | `0` | `10` | `10` | `8.020` | `2.000000` |
| Exhaustive UNSAT | `6` | `window_major` / `bit_interleaved` | no | `4,096` | `0` | `12` | `12` | `10.006` | `2.000000` |
| Exhaustive UNSAT | `7` | `window_major` / `bit_interleaved` | no | `16,384` | `0` | `14` | `14` | `12.002` | `2.000000` |
| Exhaustive UNSAT | `8` | `window_major` / `bit_interleaved` | no | `65,536` | `0` | `16` | `16` | `14.001` | `2.000000` |
| Planted SAT | `5` | `bit_interleaved` (`window_major`) | yes | `263` (`64`) | `3` (`5`) | `10` | `14` (`10`) | `9.091` | `1.993111` |
| Planted SAT | `6` | `bit_interleaved` (`window_major`) | yes | `1,035` (`256`) | `4` (`6`) | `12` | `17` (`12`) | `11.032` | `1.993111` |
| Planted SAT | `7` | `bit_interleaved` (`window_major`) | yes | `4,111` (`1,024`) | `5` (`7`) | `14` | `20` (`14`) | `13.009` | `1.993111` |
| Planted SAT | `8` | `bit_interleaved` (`window_major`) | yes | `16,403` (`4,096`) | `6` (`8`) | `16` | `23` (`16`) | `15.002` | `1.993111` |
| Planted SAT | `9` | `bit_interleaved` (`window_major`) | yes | `65,559` (`16,384`) | `7` (`9`) | `18` | `26` (`18`) | `17.001` | `1.993111` |
| Planted SAT | `10` | `bit_interleaved` (`window_major`) | yes | `262,210` (`61,837`) | `8` (`10`) | `20` | `29` (`20`) | `19.000` | `1.993111` |

**Verdict (`P1-3b` — `REFUTED_BARRIER_CONFIRMED`)**: Fixing $(x_0, x_1) \in W_0 \times W_1$ determines at most four candidate abscissae $x_2 \in \mathbb{F}_p$ via $S_3(x_0, x_1, u) = 0 \Rightarrow S_3(x_2, x_R, u) = 0$, so every theory conflict requires all $2s = (k - 1)s$ bits of two windows (or up to $3s - 1$ bits under bit-interleaved branching when $W_2$ collides on bit prefixes), forcing exact $\Theta(2^{2s})$ conflicts (`e = 2.000000` vs the sub-birthday gate `e < 0.5`) [pcc:unverified].

### 2. All-In Prime-Field Cost Floor for `CT186`-Type Chained Jacobian Transfers (`P1-4b`)

Auditing `CT186`, `CT198`, and `CT143` over a prime field $\mathbb{F}_p$ (extension degree $n = 1$, where Weil restriction yields no smaller base field $\mathbb{F}_{p^{1/n}}$):
- **Route-delta cancellation (`CT198`)**: For any chained transfer $E(\mathbb{F}_p) \to A \to J(C)/\mathbb{F}_p$, the intermediate object cost $N_2$ cancels identically in the route comparison `(C13a + N2 + C13b) - (C169 + N2) == C13a + C13b - C169`, leaving the destination Jacobian DLP floor on $J(C)(\mathbb{F}_p)$ unavoidable [pcc:unverified].
- **Destination Jacobian IC floor (`GTTD07` / Diem)**: Any homomorphism from prime-order $E(\mathbb{F}_p)$ ($|E(\mathbb{F}_p)| = n \approx p$) with trivial kernel embeds $\mathbb{Z}/n\mathbb{Z} \hookrightarrow J(C)(\mathbb{F}_p)$, requiring $\dim J(C) = g \ge 1$; for $g = 2$ hyperelliptic IC (`Gaudry 2000` basic $\widetilde{O}(p^{4/3})$, `Gaudry–Thomé–Thériault–Diem 2007` double-large-prime $\widetilde{O}(p)$) and $g = 3$ non-hyperelliptic plane quartic IC (`Diem 2006` $\widetilde{O}(p)$), the prime-field asymptotic floor is $\widetilde{\Omega}(p) \gg \Theta(p^{1/2})$ [pcc:unverified].

| Prime Bits $\log_2 p$ | Pollard $\rho$ $\log_2$ Group Ops ($\sqrt{\pi p / 4}$) | $g=2$ Basic IC Floor $\log_2$ Ops ($2 p^{4/3}$) | $g=2$ DLP (`GTTD07`) Best-Case Floor $\log_2$ Ops ($2p$) | $g=3$ Quartic DLP (`Diem`) Floor $\log_2$ Ops ($4p$) | Best-Case $\log_2$ Penalty vs Pollard $\rho$ |
| ---: | ---: | ---: | ---: | ---: | ---: |
| `31` | `15.326` | `43.252` | `32.000` | `33.000` | `+16.674` bits (`106,026x` slower) |
| `61` | `30.326` | `83.252` | `62.000` | `63.000` | `+31.674` bits (`3.47e9x` slower) |
| `128` | `63.826` | `172.585` | `129.000` | `130.000` | `+65.174` bits (`4.05e19x` slower) |
| `256` | `127.826` | `343.252` | `257.000` | `258.000` | `+129.174` bits (`7.70e38x` slower) |

---

## Reproduction Commands

```bash
export CARGO_TARGET_DIR=/Volumes/SSD990-2/wt-3858/target-cryptanalysis-aux

# 1. Unit, exhaustive m=3,4 small-prime oracle, and CDCL(T)/CT186 tests
cargo test --release --manifest-path crates/prime-field-auxiliary-ic/Cargo.toml
cargo test --locked --manifest-path suite/Cargo.toml --lib cli::tools::ic::auxiliary::tests

# 2. Regenerate deterministic CDCL(T) + CT186 receipt
cargo run --release --manifest-path crates/prime-field-auxiliary-ic/Cargo.toml \
  --example cdclt_ct186_audit \
  -- experiments/prime-field-auxiliary-ic/m34-and-3arm-20261119/cdclt_and_ct186_audit.json

# 3. Run preregistered 5-encoding / 3-arm + m=2,3,4 benchmark panel
cargo build --release --manifest-path suite/Cargo.toml --bin ca-ic
python3 experiments/prime-field-auxiliary-ic/m34-and-3arm-20261119/run_panel.py
```
