# L2c protocol: confirmatory test of the RREF effect on decomposable targets

Frozen 2026-11-18, before any solver run on these instances.

## Hypothesis (from L2b, exploratory)

L2b (`../l2b_rref/RESULT.md`) reported, outside its pre-registered decision
subset, that adding the RREF of the XOR rows as prefix-chain extension
variables cut CaDiCaL's conflicts on **decomposable (SAT)** m = 4 targets at
l = 4 to 0.358× [0.204, 0.556]. That subset was one of six and was chosen
after seeing the data. This protocol tests it as the sole decision, on
**fresh curves and fresh targets** that L2b never saw.

## Scope of a positive result

Even a confirmed effect is a statement about solver behaviour on satisfiable
instances, not an index-calculus improvement. A relation-search query costs
p·SAT + (1 − p)·UNSAT, where p is the decomposable fraction. L2b measured
UNSAT conflicts as unchanged or slightly worse (1.061×), and p is small for
the m = 4 cells. A net gain per query would need a separate argument for a
setting where most queries are SAT. Such a setting was killed earlier as
pilot idea 9 (`crypto:research/sat_smt_leads_20261114/09-solution-rich-regime`).

## Instances (frozen)

- **Generator.** `../l2b_rref/gen_l2b.py --seed-base 2026111800 --n-non 0 --n-dec 16`,
  with dr4 from crypto commit `833a35d`. `Cell4(l, 2026111800 + l)` gives a
  new curve per l, distinct from the L2/L2b cells (seed base 2026111500).
- **Targets.** `targets(0, 16)` gives 16 planted decomposable targets per
  cell, for l ∈ {3, 4}, with encodings `plain` and `dual`.
- **Count.** 64 base CNFs plus 64 RREF-augmented CNFs. SHA-256 for each are
  in `manifest.json`, generated before this freeze.
- **Shuffles.** 3 seeded shuffles each, with L2b's seed scheme: A uses
  `l2-shuffle-<file>-<k>`, C uses `l2b-shuffle-<rref_file>-<k>`.

## Arms and conditions

These are identical to L2b (`../l2b_rref/PROTOCOL.md`):

- **A:** CaDiCaL on the shuffled base CNF.
- **C:** CaDiCaL on the shuffled RREF-augmented CNF.
- **A/A:** A(k) / A(0).
- **Solver and caps:** CaDiCaL `6b3d70b` (3.1.0), default options, 600 s
  cap per call.
- **Execution:** 3 workers on the unisolated container, with A and C of a
  pair back to back.
- **Runner:** `../l2b_rref/run_l2b.py`. It re-verifies any incomplete
  printed model with `--elim=0`.
- **Correctness gate:** every answer must be SAT, and every model must be
  verified. Any failure makes the run invalid.

## Decision rule (primary: l = 4, all 32 base CNFs × 3 shuffles = 96 pairs)

Let ρ = conflicts_C / conflicts_A per pair. Take its geometric mean, with a
95% bootstrap interval from 10,000 resamples of base CNFs, seed `l2-boot`.

- **CONFIRMED** if all three hold:
  - the geometric mean of ρ ≤ 1/1.3 = 0.769;
  - the 95% upper bound < 1;
  - the ρ interval does not overlap the A/A interval of the same subset.
- **REFUTED** if the 95% interval contains 1, or the geometric mean of ρ
  is above 0.769.
- **INCONCLUSIVE** otherwise.

Reported but not deciding:

- the wall-time ratio ω (C's CNF is larger, so a conflict reduction need
  not mean a wall-time reduction);
- l = 3;
- per encoding.

## Records

- One `bench.record/v1`, with raw rows in Git under 64 KiB, written outside
  the repository during the run.
- No resume checkpoint: there is no upload token. Runs are launched with
  `CHECKPOINT_SKIP`.
- All results are `[pcc:unverified]`.
