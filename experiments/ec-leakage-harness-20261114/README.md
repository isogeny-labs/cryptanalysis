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

## Follow-ups 1–4 (`followup.py`) [pcc:unverified]

The numbers in this section come from this session's own runs and no
independent verifier has checked them yet. Each command below writes
`results/followup_<name>.json` and a matching `.png`.

- `python3 followup.py tiny`
- `python3 followup.py population`
- `python3 followup.py mov`

### 1. The linear advantage on the 12-bit curve is an artifact

On the 12-bit curve, 21,992 samples take only 1,374 distinct x-values, so each
x-value turns up in both the training and test sets. Three nulls separate what
the linear fit learns about the curve from what it simply memorises:

- **Sample-level label permutation** (5,000 permutations, as in the base run).
  Accuracy is at chance, 0.500 on the low bits.
- **x-consistent null.** A random bijection of the distinct x-values: labels
  stay a function of x but lose any curve structure. Accuracy is 0.534–0.537 on
  the low bits, which accounts for most of the observed 0.537–0.571.
- **Disjoint-x split.** The test x-values never occur in training; 50 random
  splits, 1,000 label permutations. On bits 0–8 accuracy is 0.476–0.539 against
  nulls of 0.497–0.534, which is chance. Bits 9–11 match their nulls exactly,
  because the labels are lopsided and both guess the majority.

Bits 1 and 2 sit above the x-consistent null with p = 0.010 and 0.015. Neither
survives a correction for testing 12 bits, and the disjoint split shows nothing
on either bit.

**Conclusion.** The base run's ±0.05 is the linear fit memorising x-values
that occur in both training and test. It says nothing about the curve.

### 2. Twenty curves per class at 40 bits

Each class has 20 curves, with 2,000 samples per curve. The z-score of each bit
of k\* is measured against 100 permutations; bits that are constant (the top
bit of k\*, which is always below n/2) are excluded. Group orders come from
PARI's SEA algorithm (`ellcard`), cross-checked against the harness's own BSGS
on one curve per class; all three matched.

| class | bits | mean z | sd z | fraction with \|z\| > 3 | max z (familywise p) | structured attack |
|---|---|---|---|---|---|---|
| smooth | 780 | +0.06 | 0.97 | 0.38% | 3.74 (0.07) | Pohlig–Hellman ±k mod q: 1.000 on 20/20 curves |
| anomalous | 769 | −0.01 | 1.04 | 0.39% | 3.47 (0.20) | Smart: 400/400 |
| prime | 780 | −0.05 | 1.00 | 0.13% | 2.98 (1.0) | none |

Every class matches N(0,1), which puts about 0.27% beyond |z| = 3.

### 3. Stronger generic predictors

These predictors ran on the same 60 curves. The target is
c = min(k\* mod q, −k\* mod q), where q is the smallest odd prime factor of n
on smooth curves and q = 3 otherwise.

- **Gradient boosting** (scikit-learn `HistGradientBoostingClassifier`) on the
  bits of x, x mod 2…16, the Legendre symbol of x and x/p, predicting c mod 2,
  with 20 permutations per curve.
  - Mean advantage on c mod 2: −0.001 (smooth), +0.001 (anomalous), −0.001
    (prime).
  - Mean advantage on bit 0 of k\*: +0.007, −0.001, −0.005.
  - On the smooth curves, Pohlig–Hellman predicts the same target with
    accuracy 1.000.
- **Mutual information** between x mod m (m = 2, 3, 4, 5, 7, 8, 16, q) and c,
  with 200 permutations. About 140 tests were run per class, and the smallest
  p-value was 0.005, which is what chance gives at that many tests.

**Conclusion.** Neither generic learner sees leakage that a structured attack
reads off exactly. A clean result from a generic learner is not evidence of
security.

### 4. MOV positive control

**Attempt with embedding degree 2 (abandoned).** The first version used the
supersingular curve y² = x³ + x with embedding degree 2. It did not work at
these sizes. PARI's discrete log on a prime-order subgroup of F_{p²}* scaled
like a generic method: 4 s at r ≈ 2^48 and 68 s at r ≈ 2^56, about 16 times
slower for 8 more bits. At r ≈ 2^70 a single 80-bit trial had not finished
after 10 minutes. This confirms that transferring to F_{p²} gains nothing
unless the target field has an index-calculus solver.

**Control used: embedding degree 1.**

- **Curve.** y² = x³ + Ax over F_p, with CM by Z[i] and Frobenius
  π = 1 + r(c + di). Then all of E[r] is rational and r | p − 1. The run used
  r ≈ 2^60, p ≈ 2^127 (c = 1, d = 13) and E(F_p) ≅ Z/n₁ × Z/n₂ with r dividing
  both.
- **Attack.** Start from x([k]P) only. The Weil pairing with a second,
  independent r-torsion point gives a value in F_p*, and PARI's `znlog`, which
  uses index calculus there, recovers ±k.
  - 10 of 10 trials recovered k\*, with a median of 28 s per scalar.
  - The independent check that [k]P has the original x-coordinate passed on
    every trial.
- **Negative control.** An ordinary curve with a 60-bit prime subgroup and an
  embedding degree above 200. PARI's generic `elllog` did not finish within
  the 600 s budget; rho there needs about 2^29.7 group operations.

**Scope.** This shows the transfer working and beating the generic method at
the same subgroup size, on one machine and one seed. It is not a benchmark row.

## Limits and next steps

- Permutation counts set the p-value floors: 0.005 at 200 permutations, and
  0.048 for the 20-permutation gradient-boosting nulls.
- The population covers 40-bit curves only, with 20 curves per class.
- The MOV timings come from one machine and one seed, with no isolation, so
  they are indicative only.
