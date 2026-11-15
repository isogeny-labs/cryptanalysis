# Lead 2: positive-control feature calibration for the generic learners [pcc:unverified]

## Preregistration (written before the full run)

Smoke test only (1 curve per class, 500/500 samples) preceded this text; its numbers are discarded.

- **Question.** scale.py and follow-up 3 found that linear and gradient-boosting learners, on bits of x, x mod m (2..32), Legendre(x) and x/p, detect nothing about c = min(k* mod q, -k* mod q) on 40-bit curves. Which leaks can that feature family express, and which can it not?
- **Prediction P1.** With the structure feature (bits of xs = x([n/q]Q), Q = lift_x(x)) added, accuracy on cmod2 on smooth curves is near 1.0 (matching Pohlig-Hellman), z far above 5, for both learners. On prime and anomalous curves (q does not divide n) it stays at chance (|z| mostly < 3).
- **Prediction P2.** The default features give chance (z ~ N(0,1)) on cmod2 on all three classes.
- **Prediction P3 (calibration of the default family).** A planted leak that IS a simple function of x (y = [x mod 7 < 3], independent of k) is detected by default features (HGB near 1.0), so the null on c is not caused by a dead pipeline.
- **Kill criterion.** If the struct feature does not reach accuracy >= 0.95 with z > 5 on at least 90% of smooth curves for HGB, the feature is not exposing the subgroup and no conclusion is reported until it is fixed. If default features show z > 5 on cmod2 for smooth curves, the earlier null is wrong and is reported as such.
- **Controls.** Positive: struct on smooth. Negative: default on smooth/prime/anomalous; struct on prime/anomalous; shuffled labels (z should be N(0,1)); bit0 of k* as an unrelated target. A/A: two disjoint training sets (A, B) with different learner seeds, same test set; compare accuracies and z.
- **Design.** All 60 curves of results/followup_population.json (20 per class). Train 3000 per replicate (A, B), test 3000. Samples via PARI ellmul (30 per curve re-derived with ec_leakage arithmetic). z = (acc - mu)/sqrt(mu(1-mu)/n_test) with mu the no-leakage null mean (scale.py null_z). Single core, OMP_NUM_THREADS=1.

## Results [pcc:unverified]

Run: `OMP_NUM_THREADS=1 python3 calibrate.py` (about 25 min, 1 core). Raw rows and per-cell summary: `results.json`; stderr progress: `run.err`; plot: `calibration.png` (cmod2 accuracy minus null mean, replicate A, per curve). Each cell below is 20 curves x 2 replicates (A, B) = 40 fits; "acc" is mean test accuracy over curves (replicate A and B pooled in z; accuracy means over both), "null" the mean no-leakage null accuracy (majority-weighted, scale.py formula). Test set 3000 per curve.

Target cmod2 (c = min(k* mod q, -k* mod q), q in {3,5} on 18 of 20 smooth curves (q=3 on all anomalous and prime curves), 307 and 431 on idx 15 and 18):

| class | features | learner | acc | null | mean z | min..max z | curves with z>5 |
|---|---|---|---|---|---|---|---|
| smooth | struct | hgb | 1.0000 | 0.5378 | +50.81 | +48.1..+54.8 | 20/20 |
| smooth | struct | linear | 0.9709 | 0.5378 | +47.63 | +20.1..+53.2 | 20/20 |
| smooth | default | hgb | 0.5899 | 0.5906 | -0.08 | -1.5..+2.2 | 0/20 |
| smooth | default | linear | 0.6176 | 0.6181 | -0.06 | -1.2..+1.1 | 0/20 |
| anomalous | struct | hgb / linear | 0.6372 / 0.6547 | 0.6380 / 0.6550 | -0.09 / -0.03 | -1.4..+1.1 / -0.8..+0.7 | 0/20 |
| anomalous | default | hgb / linear | 0.6296 / 0.6629 | 0.6311 / 0.6631 | -0.16 / -0.02 | -1.6..+1.1 / -0.9..+0.4 | 0/20 |
| prime | struct | hgb / linear | 0.6341 / 0.6513 | 0.6348 / 0.6514 | -0.07 / -0.01 | -1.3..+1.3 / -0.8..+0.7 | 0/20 |
| prime | default | hgb / linear | 0.6291 / 0.6588 | 0.6286 / 0.6592 | +0.06 / -0.05 | -1.1..+1.7 / -0.5..+0.3 | 0/20 |

Other controls (all 3 classes unless noted):
- **Planted default-expressible leak** y = [x mod 7 < 3] (independent of k): default features give HGB accuracy 1.0000 (z about +53.6) and linear 0.989-0.996 (z about +53) on every class. The default family can see leaks that are simple functions of x.
- **Shuffled cmod2 labels**: mean z between -0.13 and +0.06 for every class, feature set and learner (struct and default alike).
- **bit0 of k\*** on smooth curves (unrelated to c): z means -0.10..+0.26, max +2.9 (struct linear), also at chance with the struct feature.
- **A/A** (disjoint training sets, different learner seeds, same test set): on smooth/struct HGB the accuracy is 1.0000 in both replicates (z correlation 1.0, mean diff 0); linear 0.9709, mean A-B difference +0.0012, sd 0.0036, z correlation 0.99996. On null cells A-B accuracy differences have mean within +-0.005 and sd 0.003-0.016 (the binomial sd of a 3000-sample accuracy is about 0.009).
- Linear learner on struct is below 1.0 only on the two curves with large q (idx 15, q=307: 0.734/0.724; idx 18, q=431: 0.696/0.683) where the label is not a linear function of the bits of xs; HGB gets 1.000 there. The 18 curves with q in {3,5} (2-3 distinct xs values) are 1.000 for both learners.

## Verdict vs preregistration

- P1 confirmed: struct feature on smooth curves, HGB accuracy 1.000 on 20/20 curves (kill criterion required >= 0.95 on >= 90%; passed), z +48.1..+54.8. On prime and anomalous curves the same feature is at chance (|z| <= 1.4 on all 80 fits, worst case HGB).
- P2 confirmed: default features on cmod2 at chance on every class (max |z| = 2.2 over 240 fits; roughly one fit above 2 is expected by chance at that count).
- P3 confirmed: default family detects the planted x-function leak at accuracy about 1.0.
- Kill criterion not triggered.

## What this does and does not show

Shows: the earlier null on 40-bit curves is a statement about leaks expressible by bits of x, x mod m (m <= 32), Legendre(x) and x/p. A leak of the Pohlig-Hellman kind (c = k* mod q) is NOT in that family (default z about 0 on smooth curves, where PH recovers it exactly), but becomes fully visible (accuracy 1.000) once one feature, x([n/q]Q), exposes the order-q component. The positive control also proves the pipeline, the z statistic and the splitting can detect an effect of this size, at 3000 training samples. Planted simple-in-x leaks are visible to the default family.

Does not show: that any hidden leak exists on prime-order curves; the struct feature at prime order is not an attack (there is no subgroup to expose, and the result is chance as expected). The struct feature needs the group order and its factorization, i.e. it is the Pohlig-Hellman computation placed inside the feature, so detecting c with it is by construction and not a discovery. The bound is: no leak of the default feature family's expressive reach, and, separately, the learners cannot synthesize x([n/q]Q) themselves from x. Features outside both families (other isogeny images, other multiples, higher-degree functions of x, x([j]Q) for other j) are untested.

## Caveats

- Only one structure-revealing feature type and one target (cmod2; q is mostly 3 or 5, so cmod2 is nearly a full-class label there).
- Accuracy-vs-null z uses scale.py's binomial formula. When a classifier predicts nearly a constant class its z sd is below 1 (observed sd 0.2-0.7 on some null cells), so the formula is conservative there; the shuffled-label cells are the empirical null.
- The same 60 curves as follow-up 3; 3000 training samples per replicate (not the 1e6 of scale.py).
- Samples come from PARI (ellmul, ellordinate); 30 per curve are re-derived with ec_leakage arithmetic (assert passed). Smoke test run first on 1 curve per class was discarded.
- Anomalous and prime curves use m = n//q (floor) as the multiplier, so the feature is a deterministic function of x with no subgroup meaning.
- All numbers [pcc:unverified]. Nothing here is an improvement over the index-calculus baseline or Pollard rho.

## Next step

Sweep the struct feature over more targets (full class c, higher bits of k* and k* mod q^2 on curves with prime-power factors) and test a partial feature (x([j]Q) for j not a cofactor) to map how far from the subgroup structure a feature can be before detection drops; then add a hidden-subgroup-free family (isogeny-image x-coordinates) as the next candidate feature class on prime-order curves.
