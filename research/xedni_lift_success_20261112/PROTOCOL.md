# Xedni lift success per trial over toy primes: preregistered protocol (2026-11-12)

Status: frozen by sha256 (`FREEZE.json`) before any sweep row was produced.
Every number below is `[pcc:unverified]` until a pcc claim exists.

## Question

The only known cross-characteristic route for prime-field ECDLP lifts to
characteristic 0 (xedni).  Jacobson, Koblitz, Silverman, Stein and Teske
(JKSST, DCC 20 (2000) 41-64) prove a *conditional* upper bound of about `C0/p`
on the success probability of one lift.  Does the certified lift in this
repository (`ca-icx xedni-lift`, LLL + exact Babai + bounded exact
discriminant search) succeed per trial at a rate that falls like `1/p`, or does
some family of instances succeed at a rate bounded away from `1/p`?  A family
bounded away from `1/p` would be the first cross-characteristic lead; a family
that tracks `1/p` is the expected null. [pcc:unverified]

## Source of `C0`

JKSST Section 4 (Lemma 4.1 and Theorem 4.1; Theorem 4.1 opens "under certain
plausible assumptions", Lemma 4.1 assumes a uniform height/discriminant
comparison and Lang's conjecture).  The closing estimate is, as recorded in
`crypto:research/jksst_xedni_audit_20261101/README.md` (second hand: the
primary PDF is not readable in this container), "approximately
`(2*C2)^r/p`", where `C2` is a constant of the height comparison.  So `C0`
is not a universal number: it depends on `r` and on the coefficient-size
regime of the lift, and it is not computed here.  This sweep therefore tests
the **exponent**, not the constant.  For every unit below, `C0` is a free
constant, fitted by Poisson maximum likelihood; the preregistered claim is
that the log-log slope of success rate against `p` is about -1.  The
asymptotic theorem is not tested at toy size; only its predicted `1/p` scaling
is, and the audit records that the constant bound needs a bounded cofactor and
the conditional hypotheses.

## Instances and the trial

Frozen code: `sweep.py` (trial), `analyze.py` (analysis), `run_all.py`
(schedule).  Binary: `suite/target/release/ca-icx` built in release mode from
the commit in `FREEZE.json`.

For a prime `p` in `{31, 67, 127, 251, 509, 1021, 2039, 4093, 8191, 16381,
32749, 65521}` and a **curve family** in `{generic, j0}`:

* `generic`: `y^2 = x^3 + a x + b` over `F_p`, `a` uniform, `b` uniform
  non-zero, non-zero discriminant.  `j0`: `y^2 = x^3 + b`.
* A pool of 40 curves per (`p`, family), seeded from the master seed
  `xedni-lift-success-20261112`; a trial `idx` uses curve `idx mod 40`.
* A random point `P`, its exact order `n` (from the exact group order), a
  secret `l` uniform in `[1,n-1]`, `r-1` known multiples `m_i P`, and the last
  point `Q = l P`; all `r` points distinct up to sign; trials with `n < 2r+1`
  are `small_order` and excluded from the denominator (counted and reported).
* `r` in `{3,4,5,6}`.  `r=7..9` needs the ten-coefficient path, whose
  Weierstrass conversion is not implemented (`xedni_lift_optimizer` README), so
  it is out of scope; `r=2` is excluded as the degenerate pair case.
* **Lift family** in `{balanced, wide}`: balanced lifts of the coordinates in
  `(-p/2, p/2]` (the frozen p=67 fixture's choice), or balanced lifts shifted by
  an independent uniform multiple `p*t`, `t` in `{-1,0,1}`, per coordinate.
* The seven-coefficient system `B u = 0`, `u = u0 (mod p)` is solved exactly by
  integer column-HNF (`sweep.py: solve_affine`); a trial whose system has no
  integer solution or is rank-deficient is excluded (`no_integer_solution`,
  `rank_deficient`, counted and reported).  `ca-icx xedni-lift --radius 1
  --max-candidates 3^(7-r)` returns the optimized coefficient vector. [pcc:unverified]

A **unit** is one (curve family, lift family, `r`) combination: 16 units.
Trials per unit and prime: `T(p) = round(300*sqrt(p/67))`, i.e. 204, 300, 413,
581, 827, 1171, 1655, 2345, 3317, 4691, 6633, 9382; 504,304 trials in all.
Primes run ascending in `run_all.py`; a prime stage is not started after 3000 s
elapsed, and an unstarted stage is reported as censored.

## Success and its certificate

The lifted Weierstrass model is `V^2 + a1 X V + a3' V = X^3 + a2' X^2 + a4' X
+ a6'` with integer coefficients obtained from the seven coefficients by
`c3 = a0*a00`, `(X,V) = (c3 x, c3 a0 y)`; it is isomorphic over `Q` to the
optimized cubic and `= E` modulo `p`.

A trial is a **success** iff *all* of the following hold; a failed check
sets status `lift_cert_failed` or `relation_cert_failed` and is counted as a
failure of the pipeline, reported separately:

1. the lifted curve is non-singular over `Q` (exact integer discriminant);
2. its coefficients reduce to `E` mod `p`, and each lifted point lies on it
   exactly and reduces to the intended `F_p` point;
3. there is an integer vector `0 != n`, `|n_i| <= 6` (the **box**), with
   `sum n_i P~_i = O` on the lifted curve, found by a meet-in-the-middle search
   modulo a 61-bit prime and **verified by exact rational arithmetic** over `Q`;
4. a second exact evaluation of the same relation gives `O`, and the relation
   reduces to `sum n_i (m_i P) = O` in `E(F_p)`. [pcc:unverified]

Recorded per success: the relation, its weight, whether `n_Q` is coprime to
`n` and the relation then recovers `l` (`dl_recovered`).  A **line** success
is weight 3 with all `|n_i| = 1` (three lifted points collinear, equivalently
`+/-P~_i +/- P~_j +/- P~_k = O`); every other success is **non-line**.  A trial
with no relation in the box is a non-success, even if the points are dependent
with a larger relation (the box is a stated limit of the detector).
Also recorded per trial: `fp_rel`, whether any non-zero vector in the box
satisfies the relation in `E(F_p)` (a necessary condition for success).

## Controls

`python3 sweep.py selftest` must pass before the sweep: a planted relation
(`y^2 = x^3 + 1`, points `(2,3)`, `(0,1)`) is found and verified exactly; a
mutated relation is rejected by the exact check; an independent pair on
`y^2 = x^3 + 17` gives no relation in the box; all primes used are prime. [pcc:unverified]

## Estimand, model, prediction

Rate of a cell = successes / trials with status `ok`.  For a unit, or a pooled
unit (`pool/generic`, `pool/j0`, `pool/all`), fit the Poisson model `S_p ~
Poisson(T_p exp(alpha + beta ln p))` by maximum likelihood on primes `p >= 127`
(10 primes; the window is fixed to keep the smallest, saturated primes out of
the slope), with Wald standard errors.  `C0_hat` is the maximum-likelihood `C`
for `rate = C/p` (beta fixed at -1) on the same window.

**Frozen prediction.** Success tracks about `C0/p`: for the pooled units,
`beta` is near -1 (point estimate in `[-1.25, -0.75]`), and no unit is bounded
away from `1/p`.

## Decision rule

Each unit gets one class from its 99.7% interval (`z = 2.97`, Bonferroni over
the 16 units at family-wise 0.05) `[lo, hi]` for `beta`, in this order:

1. fewer than 10 successes at `p >= 127`: **uninformative**;
2. `lo <= -1 <= hi`: **tracks 1/p**;
3. `hi < -1`: **faster than 1/p** (below the bound; consistent with it);
4. otherwise (`lo > -1`): **LEAD** if at least 30 successes at `p >= 127` and
   `lo > -0.75`, else **slower than 1/p, below the lead threshold**. [pcc:unverified]

The prediction is supported iff no unit is LEAD and the three pooled units are
in class 2 or 3.  A LEAD is only a candidate: it must be replicated at larger
`p` with fresh seeds, checked for a mechanism (for example a lift choice that
makes lifted points collinear by construction, which would not be a lift
success in JKSST's sense), and priced against matched rho before any claim.
The same classification is applied to **non-line** successes as a secondary,
exploratory result (not part of the prediction).  The whole analysis is
`analyze.py`, run unchanged.

## Not tested

Whether lifted points are dependent through relations outside the box;
`r >= 7`; the ten-coefficient path; ECDLP cost against Pollard rho; any
statement about `p` beyond 65521; a hand-tuned lift (the lift is the repository
optimizer as is).  Timing is not measured as a benchmark claim; wall time is
recorded only as the compute budget.

## Waiver and records

The S3 resume-checkpoint requirement is waived for this toy-size run by the
owner (2026-11-12): "for this toy-size run only, the S3 resume-checkpoint
requirement is waived because no upload credential exists in this container."
Not waived: the benchmark record (`tools/benchrec.py`, left open), this frozen
protocol, and the certificates above.  Raw rows are not uploaded to S3 (no
credential); they are committed under `data/` and recorded by sha256.
