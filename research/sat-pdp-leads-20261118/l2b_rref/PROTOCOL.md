# L2b protocol: row-reduced XOR rows as prefix-chain extension variables for CaDiCaL

Frozen 2026-11-18, before any measured run. The only runs before freezing
were the feasibility probe below; it set the caps, and its numbers are not
data.

## Question

Lead E (`crypto:research/sat_smt_leads_20261115/E-scan-certificate-proof`)
showed that short refutations of these PDP systems exist once fresh XOR
variables are allowed: Gaussian-elimination prefix chains. Most of that
elimination is leaf-specific. The leaf-independent part is the fully
row-reduced form (RREF over GF(2)) of the system's XOR rows.

Does giving CaDiCaL those reduced rows, as redundant prefix-chain
definitions, reduce its conflicts and wall time? This is the second half of
leads-note L2: extension variables mined from lead E. Kill rule: inside the
A/A noise band. Prediction: at least a 1.3x reduction in conflicts.

## Instances (frozen)

- **Systems.** The same 48 systems as L2 (`../l2_sbva/PROTOCOL.md`):
  `dr4.Cell4(l, 2026111500 + l)` for l ∈ {3, 4}, `targets(8, 4)`, encodings
  `plain` and `dual`, from crypto commit `833a35d`.
- **Arm A instances.** The L2 base CNFs, byte-identical; this is checked
  against `../l2_sbva/manifest.json`.
- **Arm C instances.** The same CNF plus every row of the RREF of the
  original XOR rows that is not already an original row. Each added row is
  written as a prefix-parity chain:
  - P_0 = v_0, and P_j = P_{j−1} ⊕ v_j, with a fresh P_j and 4 clauses each;
  - a final unit P_k = c.
  For example, l = 4 plain t00 has 69 rows, of which 33 are added, with a
  mean length of 50 variables. `gen_l2b.py` generates the instances and
  `manifest.json` holds their SHA-256s.
- **Shuffles.** 3 seeded shuffles per CNF, k ∈ {0, 1, 2}:
  - arm A uses L2's seeds, `l2-shuffle-<file>-<k>`;
  - arm C uses `l2b-shuffle-<rref_file>-<k>`.

## Arms

- **A, baseline.** `cadical` on the shuffled base CNF.
- **C, candidate.** `cadical` on the shuffled RREF-augmented CNF. Generating
  the reduced rows takes milliseconds and is not counted.
- **A/A, noise floor.** Arm A's spread across shuffles: A(k) / A(0) for
  k ∈ {1, 2}.

## Solvers and conditions

- **Solver.** CaDiCaL git `6b3d70b9ce00` (3.1.0), default options.
- **Caps.** 600 s per call; a call that hits the cap is censored and kept at
  its recorded conflict count.
- **Execution.** 3 workers on the unisolated 4-core container. Arms A and C
  of a pair run back to back on the same worker, and the order is
  interleaved, as in L2.
- **Reproducibility check (not a gate).** Arm A's conflict counts should
  equal L2's arm-A counts exactly, because the CNF, the seed and the solver
  are all the same and CaDiCaL is deterministic. Any difference is reported.

## Correctness gate

- Every answer must match the `decomposable` flag.
- SAT models are checked with `--elim=0` re-solves where the printed model is
  incomplete, as the L2 deviation established.

## Metrics and decision rule

These are identical to L2. Primary: the l = 4 UNSAT geometric mean of
ρ = conflicts_C / conflicts_A, with a 95% bootstrap interval over base CNFs.

- **Success:** the geometric mean of ρ ≤ 1/1.3, with its interval
  excluding the A/A interval, and the geometric mean of ω (the wall-time
  ratio) < 1.
- **Kill:** ρ inside the A/A interval, or ρ above 1/1.3.
- **Otherwise:** inconclusive.

## Feasibility probe (not data)

One unshuffled call per instance:

| Instance | CaDiCaL on base | CaDiCaL on RREF-augmented |
|---|--:|--:|
| l4 plain t00 (UNSAT) | 880,596 conflicts | 472,837 conflicts, 42.7 s |
| l4 dual t00 (UNSAT) | 937,952 conflicts | 288,006 conflicts, 36.4 s |
| l3 plain t00 (UNSAT) | 13,744 conflicts | 12,197 conflicts |

The L2 probe on the same base instance also showed about 2x and then failed
on the full run. These probe numbers carry no weight.

## Records

- One `bench.record/v1`.
- Raw rows in Git, kept under 64 KiB.
- No resume checkpoint: there is no upload token. Runs are launched with
  `CHECKPOINT_SKIP`.
- All results are `[pcc:unverified]`.
