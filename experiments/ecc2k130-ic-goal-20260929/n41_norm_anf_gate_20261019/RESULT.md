# Dense left-code norm after exact right-subspace elimination

The exact right-product elimination norm on two frozen N41 target-conditioned residuals has **all 1,024 coefficients nonzero** in its ten-bit field-valued Boolean ANF, including the degree-ten coefficient. The constructed positive residual has exactly one zero left code, `253`; the ordinary residual has none. The producer checked every left code and the corresponding GCD decisions on all 281 source-valid codes. Independent checked-Sage audits built the 1,024-root right-subspace vanishing polynomial as a direct product and reproduced the full ANF digest and zero set for each row. This measured density rules out a sparse ANF for this particular left-only norm on these residuals and redirects the N131 search toward a compact shared circuit or a different jointly conditioned constraint.

## Exact construction

The field is `GF(2)[u]/(u^41+u³+1)` and the curve is `y²+xy=x³+1`, ID `EC1N41Ckb1h7d5e80d3c4d0`. The frozen W11 pair source has seed `112`, ten free canonical bits at positions `(0,1,2,3,4,6,7,8,9,10)`, and 281 source-valid first codes. The left and right pair rotations are 12 and 24. Residual index 0 is the constructed positive control with code pair `(253,63)`; index 1 is the first frozen ordinary residual. The input source is the [25-residual coefficient table](../n41_w11_freecode_resultant_20261018/resultant_input.tsv) used by the prior [full-family census](../n41_n131_macaulay_family_gate_20261019/RESULT.md).

Let `H_t(p,q)` be the pinned 13-term bidegree-(4,4) two-product eliminant for residual `t`. For a left Boolean code `a`, set `p(a)=Frob^12(x(a)²+112x(a))`; for right code `b`, set `q(b)=Frob^24(x(b)²+112x(b))`, where `x(code)` is the exact basis expansion in the runner. The right products form a 10-dimensional binary subspace `V`. Its monic vanishing polynomial is `L_V(Z)=∏_{q∈V}(Z+q)`, with 1,024 roots and 11 nonzero linearized terms. Define the left-only field value

`N_t(a)=Res_Z(H_t(p(a),Z), L_V(Z) mod H_t(p(a),Z))`.

Because `L_V` splits into distinct linear factors over the field, `N_t(a)=0` exactly when some right product in `V` is a root of the specialized quartic. The remainder resultant has the same zero set as the full resultant; its field value is the exact scalar whose ANF is measured here. This is an exact necessary condition for a valid two-pair decomposition; a zero can still require source validity and full point checks. The producer evaluates `L_V mod H_t` by modular Frobenius squaring. The independent auditors construct the entire `L_V` by multiplying its 1,024 linear factors, then use a Sylvester determinant or Sage polynomial resultant. Both compute the 1,024-value truth table and its Möbius transform into the unique multilinear ANF over the ten code bits.

## Frozen panel

| Row | Left codes covered | Norm-zero codes | Source-valid zero codes | Nonzero ANF coefficients | Maximum ANF degree | Producer wall |
| --- | ---: | --- | --- | ---: | ---: | ---: |
| Constructed positive, index 0 | 1,024 | `[253]` | `[253]` | 1,024 of 1,024 | 10 | 8.072 s |
| Ordinary residual, index 1 | 1,024 | `[]` | `[]` | 1,024 of 1,024 | 10 | 8.066 s |

The [producer result](result.json) completed both rows in 16.138 s with 256,475,136 B raw peak RSS. Every possible squarefree monomial degree 0 through 10 occurs in each ANF; the degree histogram is `(1,10,45,120,210,252,210,120,45,10,1)`. The [first independent audit](audit_result.json) verified row 0 and reached its 180 s cap after 542 codes of row 1, status `WALL_CAP_PARTIAL_AUDIT`. The [second audit](audit_result_v2.json), with a polynomial resultant replacing the generic determinant, again verified row 0 and capped after 393 row-1 codes. A separately frozen [ordinary-only audit](audit_result_v3.json) completed all 1,024 row-1 codes in 137.752 s and matched the producer's ANF digest and zero set. Both incomplete two-row attempts remain partial receipts; they are not classified as a mathematical miss on their unvisited codes.

All runs used one checked Sage process, a saved [runtime receipt](sage_runtime_info.json), a 180 s process-checked wall cap, and a 4 GiB process-checked RSS cap. They ran on an ordinary shared host. The timings are component diagnostics, not single-target online IC or matched-rho measurements. This experiment retains `candidate_id: null` because three pair slots are fixed and it does not define a complete IC pipeline.

## Proof map and next gate

The [proof map](PROOF_MAP.md) records the exact root-equivalence argument, the checked Lean ANF-butterfly lemma, and the finite-instance bridge. [ANFButterfly.lean](ANFButterfly.lean) builds under pinned Lean 4.34.1, with no axioms reported by `#print axioms`; [lean_check.json](lean_check.json) records the command and hashes. [verify.py](verify.py) checks the frozen source identities, statuses, row coverage, ANF digests, and retained cap receipts.

The measured norm is dense as an explicit ANF even though its quartic-plus-linearized-polynomial circuit is compact. Density therefore constrains **ANF expansion**, not all possible circuits or zero-equivalent equations. The next experiment should retain the right code as a structured variable while seeking a shared target-conditioned circuit or block certificate that avoids a serial pass over projected N131 W29 first codes. The N131 public-point ordinary-relation gate remains open.
