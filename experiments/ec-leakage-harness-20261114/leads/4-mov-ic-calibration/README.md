# Lead 4: MOV (embedding degree 1) as a known-answer calibration row

All numbers below are [pcc:unverified] (local, single host, single seed, no replay/validator).
**This is a WEAK-CURVE calibration, not an improvement under the success criterion.** Embedding degree 1 is a
degenerate class (r | p-1, full rational r-torsion); the row exists only so the IC tooling has a case where the
right answer (transfer beats generic) is known in advance. Nothing here touches the leaderboard or benchmarks/.

## Question
Does the Weil-pairing transfer to F_p* + PARI `znlog` (index calculus) recover k from x([k]P) far faster than
generic `elllog` on an ordinary curve with a same-bit-size prime subgroup, and how do the two scale with log2 r?

## Preregistration (written before the run)
- Prediction: transfer time grows far slower than sqrt(r) (IC-like); generic grows ~sqrt(r) (rho ~ sqrt(pi r/4) ops)
  and times out (60 s budget) by r ~ 2^60.
- Kill criterion: any wrong k (fails the against-secret check) invalidates that size; exclude and say so.
  (No size was excluded; all 25 trials passed.)

## Method (`mov_calib.py`, analysis `analyze.py`; seed 20261115+bits; OMP_NUM_THREADS=1)
- Curve y^2 = x^3 + A x over F_p, p = (1+rc)^2 + (rd)^2 prime (c,d<16), twist chosen with #E = p+1-2(1+rc);
  verified E[r] rational (ellgroup has r^2 | N, 2 generators), e(P,R) has exact order r, embedding degree 1.
- Per trial: random k; Q = [k]P; **only x(Q) is used**: lift to either sign, Weil pairing with independent R,
  `znlog(e(Q,R), e(P,R), r)`. Time = pairing + znlog (pairing is ~0.00 s; znlog dominates).
- Against-secret check: x([kk]P) == x(Q) and kk in {k, -k} mod r (the sign is unrecoverable from x alone).
- Generic baseline: ordinary random curve over F_q (q ~ r + 3..6 bits), largest prime factor of #E has exactly the
  same bit size; PARI `elllog(E,H,G,r)` under `alarm(60)`. Trials: 2 at r=40,48 bits, 1 at 56,60,64 (time box).
- Fit: log2(median time) vs bits, slope = exponent alpha in t ~ r^alpha (sqrt(r) generic/rho => 0.5).

## Results (exact, measured)
| r bits | p bits | MOV median s (5 trials, all ok) | MOV trial range s | generic elllog | rho ops sqrt(pi r/4) |
|---|---|---|---|---|---|
| 40 | 87 | 0.584 | 0.17-0.88 | finished 1.7 s, 1.2 s | 6.97e5 |
| 48 | 100 | 2.390 | 2.07-2.43 | finished 26.2 s, 8.0 s | 1.06e7 |
| 56 | 117 | 11.564 | 10.53-12.48 | TIMED OUT at 60 s (1 trial) | 2.29e8 |
| 60 | 125 | 28.312 | 26.76-29.81 | TIMED OUT at 60 s (1 trial) | 6.97e8 |
| 64 | 137 | 94.368 | 86.97-120.5 | TIMED OUT at 60 s (1 trial) | 3.42e9 |

Fits (fit.json): MOV t ~ r^0.299 over 40-64 bits; local slopes 0.254, 0.284, 0.323, 0.434 (successive size pairs),
i.e. **rising**. Generic (finished points only, 4 trials at 40/48 bits): r^0.42 (medians r^0.45); this is from just two
sizes and is not a clean sqrt(r) measurement. Plot: `time_vs_bits.png` (generic timeouts shown as open markers at the
budget, i.e. lower bounds).

## What it shows / does not show
- Shows: 25/25 correct recoveries from x only; transfer is faster than generic at every size where generic finished
  (about 3x at 40 bits, 3-11x at 48 bits) and at 56-64 bits transfer finished in 11.6-94 s where generic did not
  finish in 60 s (at 64 bits the transfer median 94 s exceeds the 60 s generic budget, so the "wins" there is NOT shown
  by this data: only at 56 and 60 bits is MOV time below the generic budget). Known-answer case works end to end.
- Does not show: that the transfer grows "far slower" than sqrt(r). The measured exponent 0.30 is below 0.5 but the
  local slope climbs toward ~0.43 and the transfer cost depends on p (~2r bits, subexponential in p), so it should
  overtake sqrt(r)-type growth asymptotically in this range of extrapolation; the preregistered "far slower" is only
  partly supported. Generic timing beyond 48 bits is censored, so the generic exponent is not established at the
  sizes that matter. No generic-beats-transfer crossover or r~2^60 generic finish time was measured.
- Not a cross-method claim: no §5a pricing of native work, no matched-rho band, no replay certificate.

## Verdict vs prediction
Correctness part: confirmed. Generic times out by r~2^56-60 at 60 s: confirmed (single trial each). Transfer
"far slower than sqrt(r)": weakly supported (alpha 0.30 fit, rising local slope 0.25 -> 0.43); not confirmed as stated.

## Controls
- Negative control: ordinary curve, same-bit-size prime subgroup, same tool family (PARI), fixed budget: done.
- Known-answer/against-secret check: every trial. Wrong-k kill criterion: never triggered.
- Not done: A/A noise-floor arm, interleaved order, masked labels, replay; one seed.

## Caveats
- The two arms differ in field size: transfer works in F_p* with p ~ 2r bits (87-137), generic in F_q with q ~ r+3..6 bits.
- Generic trials are few (1 at >=56 bits); the 64-bit transfer has 38% spread (87-121 s); 40-bit transfer has 5x spread
  (0.17-0.88 s, likely PARI znlog setup/caching or random prime-structure luck; not investigated).
- Single shared 4-core VM with four other jobs; timings are wall clock, not CPU-isolated.
- The sign ambiguity (k vs -k) is inherent to x-only input and was accepted by the check.
- Weak-curve class: embedding degree 1 curves are not cryptographically used; no inference to standard curves.

## Substitutions
No substitution beyond the time box (generic budget 60 s, <=2 generic trials; the harness's followup.py used 600 s
for a single size). The curve construction follows followup.py cmd_mov and reuses ec_leakage.py (imported, not edited).

## Next step
Run generic elllog with a longer budget (e.g. 600 s) at 52-56 bits with >=3 trials to pin the generic exponent, and
add an own rho (pi r/4 op count) baseline; then the measured transfer/generic crossover can be stated. Only then
consider an ecbench row, via the proper pipeline, as a labelled known-answer weak-curve case.

Files: mov_calib.py, analyze.py, results.json, fit.json, run.log, time_vs_bits.png (18 KB).
