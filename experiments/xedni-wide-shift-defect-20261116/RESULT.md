# Wider two-image lift grid and rational residuals

The 625-model coordinate-shift family improved the minimum rational model score on 11 of 22 frozen public relation hits, but produced zero exact rational relations in 13,750 candidate constructions. Every candidate passed the rational group-law control, and independent exact arithmetic confirmed that each nonzero relation residual has an `x`-denominator divisible by the field prime. The latter is the expected signature of a rational point reducing to the identity.

## Frozen panel and method

The [protocol](protocol.json) pins the completed, independently audited fresh-query parent by five SHA-256 digests. It admits **all 22** parent vector rows marked `public_relation=true`, ordered by event and vector index. These are conditional public hits, not a new sample of 22 targets. All have distinct image `x` coordinates. The candidate rule centers each image and enumerates the 625 shifts in `{-2,-1,0,1,2}^4` over `x1,y1,x2,y2`; each shifted pair determines one rational short Weierstrass model. This includes every candidate in the parent's 81-shift grid. The family was frozen before evaluating the wider grid.

For each model, the producer checks nonsingularity, coefficient and point reduction, and `P1+(-P1)=O`, then computes the exact rational residual `aP1+bP2` for that hit's frozen vector `(a,b)`. The raw row records the model score, zero/nonzero status, residual coordinate-height score, and a digest of the exact residual coordinates. The height score is the largest numerator or denominator bit length of the residual's `x` and `y`; it is a diagnostic for representation size, not canonical height. The [pure-Python audit](audit.py) reconstructs every curve, point, group sum, score, and digest independently of Sage.

| Stage or diagnostic | Result |
| --- | ---: |
| Frozen public hits / equal-x exceptions | 22 / 0 |
| Candidate attempts / passed / failed | 13,750 / 13,750 / 0 |
| Rational group-law controls | 13,750 passed |
| Exact rational relations | 0 |
| Nonzero residuals with `p` dividing the `x`-denominator | 13,750 / 13,750 |
| Wider minimum-model score, median | 24 bits |
| Parent selected-model score, median | 24 bits |
| Hits with improved model score in wider grid | 11 / 22 |
| Residual score at wider minimum-model choice, median | 376 bits |
| Residual score at parent selected choice, median | 358 bits |
| Minimum residual score among all 625 models, median | 286.5 bits |
| Hits where minimum-residual choice beats minimum-model choice | 20 / 22 |
| Model score at minimum-residual choice, median | 26.5 bits |

The minimum-residual choice uses the already-known successful public coefficient vector, so it is an **oracle diagnostic** of this finite family. It cannot be promoted to a vector-independent lift algorithm. Its 20 improvements show that reducing the rational model's coefficient/point size does not reliably reduce the rational relation residual. None of its 22 best residuals is the identity.

The completed checked-Sage script interval was 7.43 seconds on this ordinary host, recorded separately from launcher verification in [sage-runtime.json](sage-runtime.json). This is an algorithmic diagnostic, with no same-target timing comparison. Every attempt is retained in 22 compressed candidate parts indexed in [run-result.json](run-result.json); the [audit receipt](audit.json) is `PASS`.

## Mathematical and experimental next step

For good reduction, a rational relation would reduce to the public relation, as formalized in the parent two-image precommit proof. The converse is the construction challenge. The current finite grid supplies a stricter falsifier for coordinate shifts, while the nonzero denominator check locates every residual in the reduction kernel. A next experiment should measure the `p`-adic valuation of that residual and test a predeclared, coefficient-independent rule aimed at reducing the kernel defect; it must still check exact vanishing and charge all model-construction work.

Reproduce the evidence with `python3 verify.py`. New local Sage runs must save `/Volumes/SSD990/cryptanalysis/sage --runtime-info` and launch `/Volumes/SSD990/cryptanalysis/sage -python /absolute/path/to/run.py`; the independent audit uses `python3 audit.py`.
