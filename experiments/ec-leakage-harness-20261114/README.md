# Leakage harness for f(k) = x([k]P)

`ec_leakage.py` measures three kinds of leakage about the scalar k from the
one-way function f(k) = x([k]P). It checks the method on curves where the
leakage is known in advance. The script is pure Python plus numpy and
matplotlib, and every run is deterministic from `--seed`.

```
python3 ec_leakage.py --seed 20261114 --samples 2000 --perm 200   # ~2 min, 4 cores
```

It writes `results/results.json`, `results/per_bit_advantage.png` and
`results/output_bit_bias.png`.

## Design

- **Targets.** x loses the sign of k, so the targets are the bits of the
  sign-canonical scalar k* = min(k, n − k), the bits of raw k (to show the sign
  loss), and the class ±k mod m.
- **Predictors.**
  - A linear least-squares classifier on the bits of x. This is the blind
    learner.
  - A lookup table. On the tiny curve this amounts to brute force.
  - Pohlig–Hellman on ±k mod each small prime-power factor (smooth control).
  - Smart's p-adic attack (anomalous control).
- **Statistics.** Training and test sets are split 50/50. Advantage is test
  accuracy minus the mean of a permutation null: the labels are shuffled and
  the predictor is refit, 200 times. The p-value is one-sided, and the
  per-bit minimum is Bonferroni-corrected.
- **Controls.**

  | Control | Curve | Expected leakage |
  |---|---|---|
  | `tiny` | 12-bit, prime order | all of k* (brute force) |
  | `smooth` | 40-bit, odd order | ±k mod each factor (Pohlig–Hellman) |
  | `anomalous` | ~40-bit, j = 0, #E = p | all of k* (Smart) |
  | `prime` | 40-bit, prime order | none expected |

  The tiny curve uses 8·n samples so that the lookup table covers the group.
  The smooth curve's order is ≤ 2^12-smooth.
- **MOV.** The embedding degree is recorded for every curve, but MOV is not
  used as a computational control. At 40 bits, moving the DLP into F_{p^k}*
  gives no advantage over generic methods, so a MOV control would have
  nothing to detect.

## Results, seed 20261114 [pcc:unverified]

These numbers come from this session's own run and no independent verifier has
checked them yet.

| control | blind linear predictor: best per-bit advantage on k* | Bonferroni min p | structured predictor |
|---|---|---|---|
| tiny | +0.057 (bit 1) | 0.060 (at the permutation floor) | lookup recovers every bit of k* (accuracy 1.00); on raw k, bit 0 is at chance (0.50) because n is odd and the sign flips parity |
| smooth | +0.035 | 0.40 | ±k mod 3, 113, 1303 and 1307 all recovered with accuracy 1.000; null means 0.553, 0.019, 0.003, 0.002; p = 0.005 (the floor at 200 permutations) |
| anomalous | +0.018 | 1.00 | Smart's attack recovered k* in 50/50 test cases |
| prime | +0.036 | 0.995 | none |

**Information-theoretic checks.**

- On every control, x([k]P) = x([−k]P) holds on all 200 samples checked.
- On a 12-bit j = 0 curve with prime order (p = 3271, n = 3373), the whole
  group gives 1686 distinct x values (1.000 bit lost) and 562 distinct x³
  values (2.585 bits lost, exactly log₂6).

**Output distinguishability.** The largest monobit |z| on the bits of x is
78.5 on the tiny curve, 5.2 on smooth, 3.4 on anomalous and 2.6 on prime.
This bias is in the encoding, mainly the top bits when p is far from
2^nbits, and it does not depend on k.

**Reading.** Every planted leak was detected at the permutation-test floor.
The blind linear learner found nothing on the 40-bit curves, the
prime-order negative control included, and it also failed to find the
Pohlig–Hellman or Smart leakage. A generic learner is therefore not evidence
of security: the method is validated through its structured predictors and
its statistics, not through the learner.

One open item: on the tiny curve the linear learner's low-bit advantage of
about 0.05 sits at the permutation floor. That curve leaks k* completely in
any case. The item needs more permutations and an explanation before anyone
reads it as structure.

## Limits and next steps

- The run uses 200 permutations, so the smallest reachable p-value is 0.005.
- The experiment covers one seed and one curve per control. It is not a
  population study, and the next step is several curves per class.
- The only blind predictor is a linear model on the bits of x. Possible
  additions are nonlinear learners (for example gradient boosting on x and
  x mod small numbers) and targets of k mod m for m that do not divide n.
