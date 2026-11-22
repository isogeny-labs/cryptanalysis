# CT185 prospective falsification: ABBA/BAAB sequence-conditioned period effects

Date 2026-11-17. Evidence level: [pcc:unverified]. This protocol is frozen before the test implementation.

## Research question

Does the CT182 v2 packet-level median of eight ABBA/BAAB log ratios necessarily eliminate treatment-null bias when slot costs depend on the known deterministic packet/block sequence? Answer to be computed with the actual pinned CT182 reader's paired_statistics_v2 function, not an independently rewritten statistical estimator.

Pinned reader source: cryptanalysis PR #1711 at 92d0c646a757046f8f10a015ae17ce0ed9d0fd2c. Pinned producer schedule: CT183 PR #1713 at 39c67c946a39cecdd7ed2aa8b2d515711e5adc4c. Frozen fixture Git blob: 9ac741668dd1ffa9632ff0d58e6f4dd9f2dd18c3. Parent cross-stack source test: CT184 #1714 at 70b3aa2e276026337c52f25513b672b632a65372.

## Explicit mathematical null and deterministic nuisance schedule

Let physical A and B both have exactly the same intrinsic cost 1. For each block b and packet i, define the existing assigned order O(b,i) to be ABBA when (b+i) is even, BAAB otherwise. The first four wall-time multipliers are:

- Stationary slot-only null: (3,2,2,3) regardless of O. This must give aggregate ratio 1, with opposite order diagnostics 3/2 and 2/3.
- Order-locked period nuisance null: (3,2,2,3) on ABBA, and (2,3,3,2) on BAAB. No physical treatment-specific cost is introduced; the nuisance depends only on sequence and slot, not on the recorded route label. Both order-specific A/B ratios should be 3/2, making the proposed balanced scorer report 3/2 despite a physical null.
- Two A/A trailing controls both receive the same multiplier 3 for every block, so their absolute log ratio is 0. The CT182 packet-cluster bootstrap is expected to collapse to [3/2,3/2] in strata with multiple packets; that confidence interval does not encompass the unmodelled nuisance.
- Stationary intrinsic 5:4 positive control: physical A=5 and B=4, with stationary (3,2,2,3) slot costs. Balanced ratio must remain 5/4.

All controls use the original 48 immutable public cohort metadata and eight blocks. Matrix entries are synthetic positive integers in arbitrary time units and **are not native Rust timings or an ECDLP solution**. No false native output or PCC receipt is created. All 16 frozen strata must be evaluated separately; identity/single-packet CI remains absent.

## Falsification criteria and limitations

If sequence-locked null returns a ratio greater than 1 with both ABBA/BAAB diagnostics also greater than 1, and terminal A/A drift equal to 0, record CT182's deterministic-v2 order assignment as insufficient by itself for a causal treatment speedup claim. This does **not** prove that such nuisance occurs on any actual host. The discriminator is structural: cross-over balance cancels stationary position effects, not arbitrary sequence-conditioned latency or carryover.

Before promoting actual v2 transfer speed evidence, require a new prospectively frozen first-four-slot same-route sham (real A vs A with treatment slots labelled according to the original 4-slot order), order/timing randomization or reproducible independent order perturbations, and explicit nuisance model acceptance limits. A sham that passes is diagnostic rather than proof that every carryover is absent. These require separate budget/admission and do not alter the frozen 2,304-row source producer or v2 reader.

Scientific context: NIST/SEMATECH engineering statistics handbook on confounding (https://itl.nist.gov/div898/handbook/pri/section7/pri7.htm); Penn State STAT 509 section 12.5 on higher-order carryover and section 12.6 on randomization (https://online.stat.psu.edu/stat509/Lesson12); Reed (2012), Four Period Crossover Designs, DOI 10.22237/jmasm/1335846240. These inform the measurement design; they do not establish empirical hardware carryover.

Shared research-KB and crypto-autoresearcher vault are not available in the current runtime. Scope fallback: CT181–184 committed source, root PR #3877, queue #3904, CT125/CT176/CT182 code, NIST and the cited crossover design sources.

No native compilation, hosted benchmark, EKS/Spot/GPU allocation, branch merge, mathematical ECDLP transfer improvement or full-solve speedup is authorized or implied.
