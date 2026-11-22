# Round-4 D protocol: Macaulay solving degree of the bilinear (t; q) leaf system

Frozen 2026-11-19, before any measured cell. The only runs before freezing
were smoke tests of the instrument at n = 9, l = 3 (development; not data).

## Question

Round-4 lead D (`crypto:research/sat_leads_round4_20261116/PROPOSALS.md`)
asks whether the bilinear system has a low "first fall" or solving degree.
The system is

- S3(x1, t, xR) = 0, and
- p² + s²t² + pt + B = 0,

in the blocks t (n bits) and q = (x1, s, p) (4l − 1 bits). L4's counting
check (`../l4_minrank/RESULT.md`) showed that this link carries all the
isolating information. D's prior is 3%.

## Reformulated criterion

D's stated falsifier, "the planted solution is the unique kernel vector",
is ill-posed. The relaxed system has more than one solution: about
2^(4l−1−n), and 3 at n = 9. The well-posed criterion is this:

- For each bidegree (A, B), build the affine Macaulay matrix:
  - field equations applied;
  - rows f·m for every equation f and every multilinear monomial m of
    bidegree ≤ (A−1, B−1);
  - columns are the monomials of bidegree ≤ (A, B), ordered by total
    degree, highest first.
- After elimination, count **L**, the number of independent linear
  relations it certifies.
- Compare L with **L_max = N − dim aff(S)**, where S is the exact relaxed
  solution set. S is computed independently: x1 runs over V, t over the
  roots of E1, and (s, p) over the F2-affine solutions of E2.
- **Solved at (A, B)** if L = L_max.
- **Soundness check:** every certified linear relation must vanish on every
  point of S. A failure invalidates the run.

## Cells (frozen)

- **real:** the system above, with B and xR drawn from seed
  `r4d-<n>-<l>-<seed>`, for (n, l) ∈ {(13, 4), (17, 5)} and seeds {0, 1, 2}.
- **planted (positive control):** a random bilinear system of the same
  shape with 3N equations and a planted solution, so L_max = N. It must be
  solved at a low bidegree; otherwise the instrument is broken.
- **null:** a random bilinear system with the same shape and the same
  number of equations (2n). This gives L for a structureless system.
- **Bidegrees:**
  - (1,1), (1,2), (2,1) and (2,2) for real and null;
  - (1,1), (1,2) and (2,1) for planted at n = 17, where (2,2) costs about
    39k rows; planted at n = 13 also gets (2,2).
- **Cap:** 900 s per matrix. A matrix that hits the cap is reported as
  censored.

## Prediction and decision rule (D's, restated)

- **Prediction:** for l = 5, no bidegree ≤ (2,2) solves the real system,
  and L stays far below L_max.
- **Kill (D closed negative):** every real l = 5 cell has L < L_max at
  every bidegree ≤ (2,2), and the positive control is solved.
- **Escalate:** some real l = 5 cell is solved at a bidegree ≤ (2,1).
- **Inconclusive:** a cap is hit, or the positive control fails.

## Records

- This is an exact computation with no timing claim, so there is no
  `bench.record` (as in L3). Raw rows go in `rows.jsonl`.
- No resume checkpoint: there is no upload token. Runs are launched with
  `CHECKPOINT_SKIP`.
- All results are `[pcc:unverified]`.
