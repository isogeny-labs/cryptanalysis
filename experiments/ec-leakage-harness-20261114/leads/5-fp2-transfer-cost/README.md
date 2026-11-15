# Lead 5: the real cost of a transfer into F_p^2 (embedding degree 2)  [pcc:unverified]

All numbers below are from this session's own run; no independent verifier has checked them.
MEASURED = produced by `fp2_cost.py` (`results.json`). ANALYTIC = formula in `analytic.py` (`analytic.json`), not measured.

## Question
The harness saw PARI `fflog` solve a prime-order subgroup DLP in F_p^2* with sqrt-like scaling, so embedding degree 2 looked useless. What does PARI actually do there, and what would a genuine F_p^2 index calculus (NFS) cost, without building a solver?

## Prior art already in the tree (read-only; not duplicated)
- `/home/user/crypto/research/lead_sweep_20261110/LEAD-TRF-pairing-target-field-recost/{PROTOCOL,RESULT}.md`: prices exTNFS in GF(p^12) for BN254/BLS12-381 with memory charged (w in {0,0.5,1}), anchored at 2^128 for 3072 bits. Only k=12 pairing curves; its toy run is GF(p^2) torus rho certifying sqrt(r) scaling only (not an NFS test). Says nothing about k=2 or toy/40-80-bit sizes.
- `/home/user/crypto/research/lead_sweep_20261110/LEAD-ICP-extension-field-embedding/{PROTOCOL,RESULT}.md`: Gaudry subfield-factor-base IC on E(F_{p^2}) (embedding E(F_p) into a larger group). Counted cost p^(2-2/n) vs sqrt(p); it concerns a different transfer (curve extension, not the MOV pairing target field) and its IC cost is a formula, not a solver.
- Neither prices NFS in F_{p^2} for the order-r subgroup of a MOV transfer, nor measures PARI `fflog` on it. This lead fills only that gap. (research-kb was not queried here; sources are the two directories above.)

## Preregistration (file `PREREGISTRATION.txt`, written before the main run)
Prediction: fitted exponent e in [0.45, 0.65] (generic sqrt(r) plus PARI overhead). Kill: e clearly < 0.45 (95% bootstrap CI upper bound < 0.45) = subexponential-looking, contradicts the premise. A 28-40-bit smoke test (exponent ~0.60) was seen before the decision run and not used for it.

## Method (MEASURED part)
For r a random prime of 40, 44, 48, 52, 56 bits: p = r*h - 1 prime, p = 3 mod 4, h random small (so r | p+1, k = 2; p ends up 49-66 bits). g = random^((p^2-1)/r) has order r (norm-1 torus). Time `fflog(g^k, g, r)` for random k, 3 reps per size, check g^x = g^k, single thread, PARI 2.17 via cypari2, seed 20261114. Log-log least squares of median time vs r; 95% CI by bootstrap over reps (2000 draws).
Control: none beyond the correctness assertion and the 28-40 bit smoke run. A smooth-order positive control (Pohlig-Hellman fast) was not run; so "PARI is generic here" rests on the exponent, not on a detector check.

## Results (MEASURED, seconds; the VM was shared with 4 other jobs on 4 cores, so absolute times are inflated)
| r bits | p bits | cofactor (p+1)/r | 3 reps (s) | median |
|---|---|---|---|---|
| 40 | 49 | 464 | 0.28, 0.63, 0.22 | 0.28 |
| 44 | 55 | 1856 | 0.50, 0.31, 1.59 | 0.50 |
| 48 | 57 | 840 | 6.11, 1.71, 4.37 | 4.37 |
| 52 | 63 | 1664 | 18.02, 11.59, 12.52 | 12.52 |
| 56 | 66 | 1544 | 582.8, 271.8, 331.0 | 331.0 |

Fit of median time ~ r^e: **e = 0.627**, 95% bootstrap CI [0.523, 0.701]; endpoint exponent 0.638; a mean-based fit gives 0.605. See `fp2_cost.png` (left).
Verdict vs prediction: e = 0.63 is inside the preregistered band [0.45, 0.65], and the CI lower end (0.52) is above 0.5. The kill criterion is NOT met: nothing subexponential, no surprise. The exponent being a bit above 0.5 is consistent with sqrt(r) group operations whose cost also grows with p (field size 49 to 66 bits, p is not held fixed relative to r) plus 3-rep noise (rep spread up to 3.5x at 48 bits) and CPU contention. With 5 points and 3 reps I cannot distinguish 0.5 from 0.63 sharply; I can say it is not below ~0.5. Earlier harness figures (~4 s at 2^48, ~68 s at 2^56) are similar at 48 bits and 5x lower at 56 bits (different curve sizes, load).

## What this shows
PARI `fflog` on a prime-order subgroup of F_p^2* behaves like a generic square-root algorithm at these sizes; it is not running a real F_p^2 index calculus on the subgroup. This is a statement about PARI, not about the group.

## Analytic estimate (NOT measured) of where a real F_p^2 index calculus wins
- Formula: NFS-type DLP in F_Q, Q = p^2, medium/large characteristic with n = 2: L_Q[1/3, c] = exp(c (ln Q)^{1/3} (ln ln Q)^{2/3}) with c = (64/9)^{1/3} = 1.923 (general NFS; exTNFS (48/9)^{1/3} = 1.747 applies to composite n over medium p, n = 2 gains little; SNFS 1.526 needs special-form p). o(1) dropped.
- Key point: NFS computes the log modulo each prime factor of the group order, so cost is a function of Q only, independent of the subgroup size r. Solving the order-r subgroup costs L_Q, not sqrt(r). PARI simply does not implement that for F_p^2 subgroups.
- Calibration: anchored at 2^80 cycles for 1024 bits (a record-style anchor, 795 bits ~ 2^67.5 cycles from memory of the 2019 record, gives 2^76.6 at 1024, so the two agree to ~3 bits; the record figure is from memory, unverified). Generic side: sqrt(r) ops times 2^10 cycles per op, r ~ p ~ 2^n.
- A fixed NFS overhead floor F (poly selection, sieving, linear algebra at toy size) dominates the crossover, and I cannot calibrate it. Crossover n (curve bits; field = 2n bits): floor 2^0: n ~ 16; floor 2^30: n = 41 (field 82 bits); floor 2^40: n = 61 (field 122 bits). Both anchors give identical crossovers. At n = 128: NFS ~2^36.5-40 vs rho ~2^74; n = 256: ~2^54-57 vs ~2^138. See `fp2_cost.png` (right), `analytic.json`.
- Applicability caveat: r | p+1 with r ~ p needs trace 0, i.e. a supersingular curve. For an ordinary curve with k = 2, r | t forces r <= 2 sqrt(p), so only a sqrt(p)-sized factor of #E transfers and the rest must be solved on the curve; the sqrt(r) it replaces is then about p^(1/4).

## Conclusion
For the harness sizes (40-bit curves, field 80 bits): PARI gives no advantage at embedding degree 2 (measured, exponent ~0.6), so the harness's MOV non-control stands for PARI. A real NFS would break the same subgroup in roughly constant effort set by the 80-bit field, which by the model has a crossover somewhere around n ~ 40-60 bits (field 80-120 bits) depending on the unknowable fixed overhead, and a large win beyond (n >= 128). So the answer to "does transfer ever help" is: with a genuine F_p^2 solver, yes for supersingular (t = 0) curves above roughly 40-60 bits, and roughly marginal at the 40-bit harness curve; with PARI, never. The "no advantage until the field is far larger than toy sizes" prediction holds for PARI only, not for IC in principle: the crossover is at toy-to-small sizes, not at huge ones.

## Caveats
- 5 sizes, 3 reps, noisy; times inflated by CPU sharing (e.g. the 56-bit rep of 583 s). The 0.63 exponent likely mixes sqrt(r) with p-size growth; not decomposed.
- p is 9-10 bits larger than r (random cofactor up to 4000), not matched across sizes.
- The crossover is a dropped-o(1) formula with an unmeasurable floor; the range 16 to 61 is a sensitivity bracket, not a prediction with error bars. No NFS was run, and memory/linear-algebra pricing (the pairing-recost lead's w parameter) is not applied here.
- The supersingular-only restriction means this does not give an attack on prime-order ordinary curves.

## Next step
(1) Replace the analytic floor with a measured one: run an existing NFS-DLP implementation (e.g. CADO-NFS, if allowed) at 80-130 bit prime fields and time it, to place the real crossover. (2) Re-run this timing on an isolated core with matched p-size to settle 0.5 vs 0.6. Neither done here.

## Files
`fp2_cost.py` (run: `OMP_NUM_THREADS=1 python3 fp2_cost.py 40,44,48,52,56 3 results.json`, about 20 min), `results.json`, `run.log`, `analytic.py`, `analytic.json`, `plot.py`, `fp2_cost.png` (30 KB), `PREREGISTRATION.txt`.
