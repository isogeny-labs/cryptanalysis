# Hecke-free controls, fixed after the first six-arm result

2026-10-30. The first audit (runs/20261030T030848Z) reached rank 63 both
with equality rows and with doubling rows added to the rank-52 baseline.
It also observed all 11 projected subgroup elements. These are discovery
inputs for this follow-up, not a claim of an independent holdout.

Question: does rank closure require any Hecke information on this fixture?
Keep the same pinned source and modulo 11. Independently compute ranks of
projected equality rows only, doubling rows only, and doubling+tripling rows
only. Compare with the prior combined arms, using dense and frozen sparse
elimination. Do not optimize multiplier choice or select subsets after timing.
No speed or scalable IC claim; one finite fixture, 60-second cap.

Independently replay every prior normalized log by converting to the short
curve X=x-1/3, Y=y+1/2, Y^2=X^3-(31/3)X-2501/108 over F367.
Use a separate short-Weierstrass group law and repeated-addition multiplication,
not the audit's generalized-curve double-and-add path. Check all raw points,
all projected points, all new rows and all four prior anchored solutions.
Fail closed on any disagreement. Preserve command, source hashes and receipt.
Launch only after the unchanged checkpoint gate succeeds; checkpoint results.

If doubling alone has rank 63, report this fixture's rank closure as attainable
without Hecke rows. The next discriminator becomes larger sparse projected
bases with matched generic controls and verified target descent; do not label
this as an improvement over a Hecke-free baseline. If it does not, report
the exact residual rank and identify what the Hecke rows supplied. Neither
outcome proves a scaling law or impossibility on other classes.
