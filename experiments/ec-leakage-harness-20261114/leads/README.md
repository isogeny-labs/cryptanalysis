# Leads 1–5 [pcc:unverified]

Five follow-up leads, each run by a Sonnet agent in its own folder. Each
folder has its preregistration, script, results and README. The main session
spot-checked each result against its files and re-ran lead 1.

| Lead | Folder | Result |
|---|---|---|
| 1. Twist (invalid-point) attack on an unvalidated x-only ladder | `1-twist-leakage/` | 5/5 full key recovery on a weak-twist 40-bit curve, 0/5 on a twist-secure control. Census: 10/60 harness curves have 2^16-smooth twists. |
| 2. Feature calibration for the generic learners | `2-feature-calibration/` | The subgroup feature x([n/q]Q) gives 1.000 on 20/20 smooth curves; default features stay at chance everywhere. Bounds the earlier null to the default feature family. |
| 3. Constant-time audit of `ca_group_mul` | `3-constant-time-audit/` | Variable-time, \|t\| in the thousands; planted-leak control caught 6/6. Expected for an attack library that never handles secrets. |
| 4. MOV (embedding degree 1) calibration | `4-mov-ic-calibration/` | 25/25 transfers recovered k at r = 40–64 bits; fitted r^0.30, local slope rising to 0.43. Generic hit its 60 s budget from 56 bits. Weak-curve calibration only. |
| 5. Cost of a transfer into F_p² | `5-fp2-transfer-cost/` | PARI `fflog` on an F_p² subgroup scales generically (r^0.63, CI 0.52–0.70). An analytic NFS estimate puts the crossover at 40–60-bit curves; that figure is an estimate, not a measurement. |
