#set page(paper: "a4", margin: 1.7cm)
#set text(size: 9.5pt)
#set par(justify: true)

= Index calculus in $(ZZ\/p ZZ)^*$: half the instructions

*Date:* 2026-11-03. *Repository:* `aburan28/cryptanalysis`, study `experiments/ic-halve-20261103/`. *Class:* engineering. *Instrument:* Callgrind instruction counts (deterministic) and the performance index's paired wall comparison on a shared 4-vCPU cloud VM, CPU 3 pinned, L0 (not Tier 0 or Tier 1). *Target:* halve the instructions of `src/indexcalc.c` and `src/linalg.c`. Every computation is exact and returns `main`'s values: identical fingerprints on all six index-calculus kernels and identical `ca ic` output (relations, Lanczos iterations, logarithms).

== What changed

*Lanczos* (`src/linalg.c`): $A^T$ in CSR built once per call, so $A^T w$ is a gather; 64-bit gathers when $K(2q-1) < 2^64$ ($K$ the largest row or column sum of $|"val"|$), each sum biased by $K q$ and reduced together with the diagonal by one Shoup product; otherwise 128-bit gathers with one signed `imul` a term, unrolled by four, and a Montgomery reduction folded into the Shoup product by $2^64 D_i mod q$; the three dot products and the two vector updates of a step fused, with division-free reductions. *Dense solve*: Crout's order of the same elimination below $2^63$, each echelon entry one 128-bit dot product and one reduction (same pivots, same singularity, the unique solution); forward elimination with back substitution above. *Smoothness test* (`src/indexcalc.c`): the $q^2 > v$ stop kept as an index and searched again only when a division shrinks $v$; the scan four primes a step with one branch.

#figure(image("figures/ic_ir_and_wall.svg", width: 100%),
  caption: [Recorded values (`data/measurements.json`): instruction ratios (main / this change) and paired wall speedups with 95% CIs (7 rounds).])

== Measurements

#table(
  columns: (auto, auto, auto, auto, auto),
  [*kernel*], [*main Ir*], [*this Ir*], [*Ir ratio*], [*wall*],
  [`c_ic_precompute_zp44`], [428,257,845], [186,517,609], [*2.30×*], [1.88×],
  [`c_ic_log_zp44`], [52,139,182], [21,721,434], [*2.40×*], [1.31×],
  [`c_ic_randexp_zp36`], [53,065,586], [26,271,981], [*2.02×*], [1.18×],
  [`c_dense_solve`], [40,035,301], [13,477,809], [*2.97×*], [8.80×],
  [`c_linsolve_sparse` (61-bit $q$)], [205,043,666], [109,008,366], [1.88×], [1.76×],
  [`c_ic_precompute_zp52` (whole run)], [4,944,223,933], [2,094,670,815], [*2.36×*], [—],
  [`ca ic` lsieve, 52-bit $p$ (whole)], [3,041,121,260], [1,286,816,943], [*2.36×*], [—],
)

Every `dlp` and `field_ec` kernel is unchanged (1.000). `c_linsolve_sparse` (a 61-bit modulus, the 128-bit gather at five instructions a term) falls short of 2×; index calculus as `ca ic` runs it uses the large prime of $p - 1$ and takes the 64-bit gather. `ctest` 19/19, ASan+UBSan, TSan, clang-tidy, gcc `-fanalyzer` and clang-format pass; the existing linear-algebra tests cover every new path (moduli near $2^32$, $2^60$, $2^63$ and $2^64$).
