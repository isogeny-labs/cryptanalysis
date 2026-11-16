# CT153 prospective protocol — independent original q223 cold BSGS/rho reference

Date: 2026-11-16 UTC. Root crypto#3877; stack cryptanalysis#1589. Status: **[pcc:unverified]**.

## Purpose and negative-space control
Measure two complete **source-only** public-target logarithm recovery procedures on CT152's independently counted original `E/F_(223^3)` (not the separate nu12 source): fresh-table baby-step/giant-step and a bounded restarted three-way Pollard rho. These are comparison controls for future norm-point reuse, **not a transfer candidate** and not a demonstration of an advantage. Do not equate ordinary three-way rho with optimized negation-map rho, and do not treat same-process means as cold end-to-end measurements.

## Frozen instance
`K=F_223[z]/(z^3-3)`, `a2=(127,56,199)`, `a4=(152,35,36)`, `a6=(212,109,150)`, `G=((162,197,140),(45,11,207))`, prime subgroup `ell=2773073`, full group `4*ell=11092292`; source identity and point count: CT152. Fixed public fixture scalars: `1,17,12345,159273,2300011,2773072`. The implementation must derive `Q=[k]G` in a fixture-only layer and pass **only** `(E,K,G,Q,ell)` to either solving routine. All outputs must independently verify `[answer]G=Q` and `0 <= answer < ell`. Fresh baby table per solve; no reused/precomputed target-dependent data. If ordinary rho loops, record bounded restart failure rather than falling back silently.

## Prospective bounded execution
Independent, dependency-free C++17 field/group implementation, not the CT152 source code; explicit inversion by a^(q^3-2), no producer native imports; on-curve/order checks. Shell/Python harness launches every arm in a **fresh process**, alternates ABBA / BAAB across four blocks and all six scalars; each solve process produces JSON with domain/group/output/validation hashes, source primitive counts, solver `ns`, whole process wall `ns`, and observed peak RSS. Report raw rows, A/A drift, median paired differences, negative or null results, local CPU/environment and uncertainty limits. This is a Tier-3 exploratory CPU reference unless isolated placement, same-host real-transfer arm, admission and independent PCC exist. No unapproved EKS, GPU, paid compute, or CI launch of heavy timing.

## Fail-closed controls
Reject changed curve coefficient/field modulus, wrong generator/order, off-curve public Q, out-of-subgroup Q, wrong recovered scalar, malformed input, incomplete ABBA, changed known-answer outputs, and silent rho restart failures. For rho use the public-Q point as input, never the planted scalar; include coefficients (a,b) for `aG+bQ` and independent source verification after collision inversion.

## Interpretation and follow-up
Record whether BSGS or three-way rho is cheaper **on this same original q223 source**, but both remain source-reference arms and neither is automatically the strongest available baseline. Continue original/reuse 695/701 parity audit and separately admitted same-host `C169,C13a,C13b,D`, matched optimized rho/BSGS/IC and complete Jacobian transfer including setup, transport, LA, verification, peak RSS, signed PCC. Native source is the evidence location; no partial speedup claim.

Sources checked: cryptanalysis#1589 CT152 full source census, #1537 CT129 alternate-nu12 unexecuted BSGS screen (different source), #1562 primitive pricing (native skipped), crypto#3877/#4215/#4178. Shared research-KB service and local atlas CLI unavailable in this runtime; no novelty claim.
