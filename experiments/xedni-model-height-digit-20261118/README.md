# Exact model-height scoring for Hensel digits

## Measured result

A precommitted selector scored every admissible signed-digit tuple within
two radii of the smallest feasible Hensel radius by the height of its
interpolated rational curve and points. On the same public relation as the
two parent experiments, it reaches 313-adic depth 8 with a 207-bit model.
That is 28 bits below the short-digit path and 2 bits above the first-axis
path at depth 8. It improves the first-axis model height at five of the
seven new depths. The exact residual remains nonidentity at each depth.

| Depth | First axis | Short digit | Model scored |
| ---: | ---: | ---: | ---: |
| 1 | 23 | 23 | 23 |
| 2 | 54 | 32 | 22 |
| 3 | 74 | 69 | 40 |
| 4 | 102 | 100 | 82 |
| 5 | 119 | 102 | 106 |
| 6 | 148 | 150 | 157 |
| 7 | 177 | 200 | 157 |
| 8 | 205 | 235 | 207 |

This result distinguishes three objective functions on one fixed public
relation: first-axis cancellation, smallest signed digits, and smallest
current rational model. None of the greedy rules minimizes final height
at every depth. The next concrete test is a bounded beam search that
retains several low-height states through the full depth horizon, with
candidate admission and final selection frozen before execution.

## Method and verification

The public hit is pinned by the parent results: `p=313`, `q=331`, target
scalar `w=300`, offsets `(0,13)`, points `(15,174)` and `(236,132)`, and
relation vector `(5,4)`. At each depth, the runner computes the four
coordinate derivatives of the exact rational formal parameter modulo
`p^(k+1)`. It finds the smallest feasible signed-digit radius at most 8,
then enumerates all cancelling tuples through radius `h+2`. Before testing
any resulting group residual, it scores the interpolated `A,B,P1,P2` by
the maximum numerator or denominator bit length. It selects the minimum
`(model_bits, max_abs_digit, sum_abs_digit, signed_tuple)`.

The run recorded 165 admissible tuples across seven steps. The independent
`audit.py` exhaustively reconstructs every tuple, coefficient, score,
minimum-radius certificate, derivative probe, and accepted group sum using
pure-Python `Fraction` arithmetic. `audit-result.json` records a pass.
The baseline [Lean height-divisibility theorem](../xedni-hensel-height-20261118/formal/HeightDivisibility.lean)
continues to apply only with an exact numerator-height bound; this run is an
empirical comparison of selection policies and adds no universal theorem.

## Reproduction

Run from the repository root with both parent results checked out:

```sh
/Volumes/SSD990/cryptanalysis/sage --runtime-info > experiments/xedni-model-height-digit-20261118/runtime-info.json
/Volumes/SSD990/cryptanalysis/sage -python experiments/xedni-model-height-digit-20261118/run.py
python3 experiments/xedni-model-height-digit-20261118/audit.py
```

`protocol.json` pins the normalized parent result digests and the exact
candidate law. `runtime-info.json` identifies the accepted Sage build.
`run-result.json` retains all probes, candidates, scores, selected shifts,
and exact rational residuals. The run timing is a construction diagnostic,
not a paired IC/rho performance measure.
