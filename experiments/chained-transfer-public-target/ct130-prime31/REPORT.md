# CT130: ordinary p=2^31−1 transfer cost diagnostic (2026-11-15)

**Standing:** exploratory, retrospective, producer-only, `[pcc:unverified]`. This is NOT a complete chained-Jacobian attack, a rho frontier win, a signed result, or benchmark admission. It is a small independent **actual finite-field ECDLP** screen of whether an ordinary degree-2 isogeny changes cold BSGS cost. It does **not** replace or duplicate concurrent original degree-169, original-prime, genus-2 or norm-reuse branches.

## Exact curve and mathematical checks

Let `p=2147483647=2^31-1`. On

`E: y^2=x^3+829286810*x^2+1720850223*x` over Fp,

use rational kernel `T=(0,0)` of order 2. The classical degree-2 Vélu map is

`phi(x,y)=(x+a+b/x, y*(1-b/x^2))`, with `phi(T)=O`,

onto `E': y^2=x^3-2a*x^2+(a^2-4b)*x` (coefficients 488910027, 790354208 modulo p).

The fixed generator is `G=(340312345,363681553)`, `q=1073779747` prime, `[q]G=O`, `G != O`. The curve is nonsingular and `j=105590812`, neither 0 nor 1728. Rational 2-torsion and the independent q-torsion imply `2q | #E(Fp)`. The Hasse interval contains `2q=2147559494`, and its width is <2q; therefore the group order is **exactly 2q**. This is an ordinary prime-index-two toy curve, not a deliberately weak smooth-order example. These finite arithmetic checks were rerun using the separately written auditor; its proof standing is producer-only.

Directly checked on scalar targets 1,2,17,12345,456789 and q−1 that `phi([m]G)=[m]phi(G)`. The symbolic equality defining the codomain was also independently simplified to zero over the rationals with SymPy; it is a standard degree-2 isogeny, not new mathematics. Prior work: cryptanalysis #1500 (F101 direct transfer loss), #1537 (q223 degree-169 native screen, not run yet), crypto #4215, #3877 and BMSS (2008) https://arxiv.org/abs/cs/0609020. Research-KB MCP and checkout-local wrapper unavailable; no novelty or absence claim.

## Bounded real-workload comparison

A deterministic original-curve point-count search used seed 137 and found the above cofactor-2 ordinary curve in 13 attempts. Run **one fresh-table BSGS for each public target on E and a fresh-table BSGS after mapping BOTH G and Q to E'**. Each arm verifies the recovered log on the source; targets 17, 12345, 456789; four ABBA/BAAB blocks per process, 8 real BSGS solves per arm/target. Width 32,769 (the same q in both groups). Raw wall-ns and group-operation/inversion counts recorded for each invocation. Four separately executed source processes each recorded 24 source and 24 transferred solves. Source setup, table and per-process peak RSS are recorded; data are not isolated CPU/CI/EKS receipts.

Final checked-source process medians of `T_source/T_transferred`, by run:
`1.074702, 1.024919, 1.021428, 0.993149`.
**The sign changes between runs.** The exploratory ratio is therefore near parity, not a credible reproduced gain. On the first three runs the median of 12 per-block source comparisons is computed separately each run, not treated as 36 independent instance draws. Three-run medians of per-block-arm means were about 95.8 ms source and 91.2 ms transferred; this is diagnostic, not a statistically justified speedup.

An additional deterministic **non-optimized** 16-jump distinguished-point Pollard-rho baseline, two seeds per target/arm (source and transferred), checked all public logs on original E. Its timing changes substantially with random walk length; it is **not the strongest matched rho** and does not replace a full matched frontier. No existing prime-field index-calculus pipeline was run on this curve. In particular no complete advantage against optimized rho/BSGS/IC is claimed.

## Reproduction and validation

```sh
python3 -O ct130_experiment.py > run1.json
python3 -O ct130_experiment.py > run2.json
python3 -O ct130_experiment.py > run3.json
python3 -O ct130_rho.py > rho.json
python3 ct130_validate.py run1.json run2.json run3.json rho.json
python3 -O ct130_validate.py run1.json run2.json run3.json rho.json
```

Exact committed Python Git blobs: `ct130_experiment.py 2afbf58346040b44e92d040619e91d9ad4c23c23`, `ct130_rho.py d139b99b2515ab08470e9209611f0e613f5a1289`, `ct130_validate.py 7912a6e70b773af2489c9e4567152d0326e15499`. The final scripts were run locally in normal/optimized mode; **eight real-input mutations** (drop row/block, wrong q/source point/codomain/sequence/standing, zero timing) rejected in both modes. The verifier does not import producer arithmetic, but it is a producer-written audit, not independently signed PCC.

Local raw-data SHA256 for the four final checked-source processes:
- run1 `8bddbde7da4f716554a8b9ac3c9f9a0c59b942973e96cb96eddf1f51e5a96991`
- run2 `165b2fc9da675e3cde9b59042c55a79fe04d83b13442a56ebdc6677f60567792`
- run3 `379319c3caa3857eb65d946c49db0378c1c642316c8b3bca7442f56d16d68fd6`
- run4 `716a16ff6fbcdd3147ab805e6aa496e9b91779bda29ad7ebe4db9afec2933c8f`
- checked-rho `4830beae85ea6b586cd1d229bb37266149c5f337909769d606ca62458ebc1f26`
- independent-audit output for first three `fccf43433a6ef1183e07e9cf17b1c67f0aff714006561d199f5042f8a0f636a0` (later audit hardening changes output schema only if necessary).

The raw receipts remain in this producer's working artifact sandbox; they have **not** been entered into the PCC ledger, signed by an independent verifier or uploaded to the repository. Results must not be promoted as fully reproducible external measurements until raw bytes are published/replayed on the same frozen protocol.

## Discriminating next gate

The degree-2 control offers no established margin to pursue as an attack. Return priority to actual native #1534 `C169/C13a/C13b/D` pricing and #1523 original 695/672 whole-record norm reuse; finish #1537's q223 full source-vs-isogeny BSGS screen **with its true finite-field costs**, then optimized source rho and the matched IC frontier, all cold setup/transfer/verification/memory counted. The concurrent root #3877 Phase B 701-record source-prime oracle repair has priority over new symbolic transfer certificates. No paid host, auto-merge, or protected merge was invoked in this experiment.
