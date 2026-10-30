# Prospective residue-first source order reaches a rank-33 cap at p78157

The frozen selection rule chose (p=78157), (v=279), (#E(F_p)=78180), and largest subgroup-order prime (q=1303) before any degree-13 lift. The D79 class has 40 points and order-five projection counts 20 at residue 0 and 20 at residue 1. The trained order visited all 20 residue-1 sources before residue-0 sources. The base-plus-direct relation matrix had rank 32 over (F_{1303}); all 40 source lifts and 194 signed Hecke candidates raised it to rank 33. The frozen rank-39 stop was not reached.

| Sources lifted | New order Hecke candidates | New order rank | Old round-robin candidates* | Old round-robin rank* |
| ---: | ---: | ---: | ---: | ---: |
| 5 | 0 | 32 | 0 | 32 |
| 10 | 0 | 32 | 0 | 32 |
| 15 | 0 | 32 | 3 | 32 |
| 20 | 0 | 32 | 10 | 32 |
| 25 | 10 | 32 | 28 | 32 |
| 30 | 45 | 32 | 56 | 33 |
| 35 | 106 | 33 | 109 | 33 |
| 40 | 194 | 33 | 194 | 33 |

*The old order was computed after the prospective run reached 40 sources, using its complete source receipts. It is a descriptive replay, not a separate timed source-lift execution.

The independent checked-Sage audit confirmed the selected prime from the prescreen rule, rebuilt the 40 curve points and order-five projection, enumerated 209 direct relations with Sage point arithmetic, verified all 40 source equations and 194 Hecke rows, and recomputed every rank checkpoint for both source orders. Every source lift ended with `OUTSIDE_CLASS_TRACE`; the run status is `CAP40_RANK_DEFICIT` with six relation dimensions below the 39-rank readiness gate.

The post-run support audit found that **193 of 194 Hecke candidates use exactly two residue-1 and two residue-0 sources**; the remaining candidate uses four residue-0 sources. This composition accounts for the zero candidates during the trained order's first 20 lifts and for the old round-robin order exposing candidates earlier. It is an explanation of this recorded class, not a pre-lift predictor.

The audited support list and class residues also have a checked Lean finite certificate: all supports have four increasing indices, 193 have two residue-1 indices, one has none, and no support has four. The matrix-rank values remain independently Sage-checked finite computations; their full Lean formalization is open in `PROOF_MAP.md`.

| Recorded component | Observed time |
| --- | ---: |
| Direct relation enumeration | 1,330,839,292 ns |
| Sum of 40 degree-13 source-lift intervals | 863,743,290 ns |
| Sum of eight Hecke enumeration checkpoints | 2,867,815,417 ns |
| Sum of eight rank checks | 19,530,167 ns |

These are local stage diagnostics with the checked Sage runtime receipt; they are not a calibrated online comparison. The new order was trained on the earlier p63317/p68437 source pattern and failed this prospective holdout. The narrower next hypothesis is that cheap class/projection and direct-rank data should decide whether degree-13 lifting is likely to bridge a large rank gap before choosing a source order.
