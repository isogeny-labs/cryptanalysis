# L2 protocol: SBVA preprocessing before CaDiCaL on m = 4 PDP instances

Frozen 2026-11-18, before any measured run. The only runs before freezing
were the feasibility probe below; it set the caps, and its numbers are not
data.

## Question

Does structured bounded variable addition (SBVA) reduce CaDiCaL's conflicts
and wall time on the CNF form of the m = 4 dual-rail point-decomposition
system? The source is leads note L2 (`../README.md`). Its kill rule:
conflicts and wall time inside the A/A noise band. Its prediction: a
reduction of at least 1.3x in conflicts, with no change in exponent.

## Instances (frozen)

- **Generator.** `gen_instances.py` imports
  `crypto:research/sat_smt_leads_20261115/A-dualrail-m4/dr4.py` unchanged, at
  crypto commit `833a35d21ec2368ab081b2083d7762ed0bfd2bbc`.
- **Cells.** `Cell4(l, 2026111500 + l)` for l ∈ {3, 4}, so n = 13 and n = 17.
- **Targets.** `targets(8, 4)` gives 8 non-decomposable targets (UNSAT) and
  4 planted ones (SAT) per cell, the same targets as the 2026-11-15 pilot.
- **Encodings.** `plain` and `dual`, from `render()`. XOR rows are expanded
  by Tseitin chaining with cut length 4. That makes 48 base CNFs, listed by
  SHA-256 in `manifest.json`.
- **Shuffles.** Each base CNF gets 3 seeded shuffles, k ∈ {0, 1, 2}: a random
  variable relabelling, clause order and literal order, from seed
  `l2-shuffle-<file>-<k>`. Shuffles are satisfiability-equivalent; they
  sample solver-trajectory noise.

## Arms

- **A, baseline.** `cadical` on shuffle k.
- **B, candidate.** `sbva -i shuffle_k -o out` with default settings
  (ThreeHop tiebreak, no replacement limit, 60 s timeout via `-t 60`),
  followed by `cadical` on the output. Arm B's wall time includes SBVA's.
- **A/A, noise floor.** Arm A's own spread across shuffles. For each base
  CNF, the A/A ratio is A(shuffle 1) / A(shuffle 0) and A(shuffle 2) /
  A(shuffle 0).

## Solvers and conditions

- **Solvers.** CaDiCaL 3.1.0 (git `6b3d70b9ce00`), default options, and
  SBVA git `35e74d0`, built with clang++ -O3 against Eigen 3.4.0.
- **Caps.** One call per process, 600 s wall cap. A call that hits the cap
  is censored: it is recorded as such and kept in the summary at the cap
  value, flagged.
- **Execution.** 3 concurrent workers on a 4-core shared container, with no
  isolation. Wall times are exploratory. Conflicts are the primary metric
  because they do not depend on the host. The order of calls is
  interleaved, and arms A and B of a pair run back to back on the same
  worker.

## Correctness gate

- Every arm's SAT/UNSAT answer must match the instance's `decomposable` flag.
- A SAT model from arm A must satisfy its shuffled CNF; this is checked by
  the runner.
- SBVA output is equisatisfiable by construction, so only the answer is
  checked for arm B.
- Any mismatch invalidates the run (status `invalid`).

## Metrics and decision rule

- **Per pair.** ρ = conflicts_B / conflicts_A, and ω = wall_B / wall_A.
- **Primary.** The geometric mean of ρ over UNSAT instances (8 targets × 2
  encodings × 3 shuffles at l = 4), with a 95% bootstrap interval that
  resamples base CNFs.
- **A/A band.** The geometric mean of A(shuffle j) / A(shuffle 0) over the
  same instances, with the same bootstrap.
- **Success**, a measured improvement: the l = 4 UNSAT geometric mean of
  ρ ≤ 1/1.3, with its 95% interval excluding the A/A interval, and the
  geometric mean of ω < 1.
- **Kill:** the geometric mean of ρ falls inside the A/A interval, or it is
  above 1/1.3.
- **Otherwise:** inconclusive. l = 3 and the SAT targets are reported, but
  they do not decide.

## Feasibility probe (not data)

On one instance each:

| Instance | CaDiCaL conflicts | SBVA → CaDiCaL conflicts |
|---|--:|--:|
| l3 plain t00 (UNSAT) | 13,744 | 12,145 |
| l3 plain t08 (SAT) | 2,275 | 12,274 |
| l4 plain t00 (UNSAT) | 880,596 | 454,587 |
| l4 dual t00 (UNSAT) | 937,952 | 614,566 |
| l4 plain t08 (SAT) | 126,573 | 147,443 |

SBVA took 0.02–0.03 s per instance. These numbers set the 600 s cap.

## Records

- One `bench.record/v1`, under `tools/benchrec.py`.
- Raw JSONL in Git if under 64 KiB; it cannot go to S3 from this container,
  which has no AWS credentials.
- No resume checkpoint: there is no upload token. Every run is launched
  with `CHECKPOINT_SKIP`, with that reason.
- All results are `[pcc:unverified]`.
