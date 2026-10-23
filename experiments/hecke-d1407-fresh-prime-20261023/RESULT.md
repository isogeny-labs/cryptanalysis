# The D = −1407 signed-floor rank model replicates at a second prime

At `p = 20407`, the checked-Sage D = −1407, conductor-6 class walk has **384 rational X₀(11) points, 288 verified degree-2/3 Hecke rows, full rank 240, and nonfloor projected rank 206**. All four values were frozen in `protocol.json` before the run, using the earlier `p = 12763` result as the prediction. The new prime has trace parameter `u = 176`, since `u² − 4p = −1407 · 6²`. The two-sheet gate found 48, 48, 144, and 144 points in conductor strata 1, 2, 3, and 6, with no exceptions.

| Quantity | Frozen prediction | Fresh-prime result |
| --- | ---: | ---: |
| Class points | 384 | 384 |
| Degree-2 / degree-3 rows | 192 / 96 | 192 / 96 |
| Full row rank | 240 | 240 |
| Nonfloor projected rank | 206 | 206 |
| Signed norm-2 components | 12 | 12 |
| Exact degree-3 floor pairs | 24 | 24 |

The producer used a source-frozen copy of the regularized D1407 evaluator. `audit.py` independently reconstructs each saved point and row, checks the point's endomorphism conductor and degree-2/3 modular-polynomial root counts, verifies the elliptic-curve group relation, and computes ranks over ℚ and three prime fields. `floor.py` replays the signed cycles and floor-pair differences. The pure-Python `validate.py` checks all frozen source digests and receipts, then independently recomputes full and projected modular ranks. All three audits passed. `sage_runtime.json` records the checked launcher before the measurements.

The fresh class does **not** contain the exceptional regular point `(16 : 60 : 1)`. A separate direct probe evaluated both `x = 16` sheets at `p = 20407`: the regular point maps to `j = −121 ≡ 20286`, appears in the computed rational fiber, and the cusp is excluded. The elliptic curve with that `j` has trace 230 and endomorphism conductor 1 here, while the selected class has absolute trace 176. Thus this run independently checks the regularized evaluator at another prime and replicates the class-rank geometry; the original `p = 12763` experiment remains the class-walk case in which the branch changes the matrix.

The full-rank and projected-rank results are stage diagnostics for this fixed class, with `candidate_id: null` and `timing_claim: null`. The remaining uniform class-action argument must identify the two rational sheets and signed floor relations with ideal-class cosets for general admissible fields. A direct next test is to preselect a second prime for which the `j = −121` trace equals the chosen class trace, then freeze its branch-sensitive matrix prediction before production.

Run all Sage scripts through `/Volumes/SSD990/cryptanalysis/sage -python`. The exact outputs and scripts are hash-bound by `SEAL.json`.
