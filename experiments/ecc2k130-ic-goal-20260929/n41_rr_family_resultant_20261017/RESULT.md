# Target-conditioned quartic resultant for N41 pair-code families

**The exact Riemann–Roch quotient rejected 1,295 of 1,296 eligible N41 code-family pairs before enumerating their signed-state combinations.** Each of the two free slots contributed 36 eligible families of four signed pair states. The sole compatible family pair, codes `(6,196)`, contained state pair `(12,122)`, the independently replayed relation completion. A linear-span relaxation rejected zero family pairs because every family's four signatures spanned the full two-dimensional quotient. This separates the information preserved by an exact finite root set from the information lost by its linear hull.

## Operator and frozen panel

The [prior quotient](../n41_rr_two_slot_quotient_20261016/RESULT.md) fixes four pair-output states in slots 2–5 from an archived relation and includes the public point as a fifth Riemann–Roch row. Its two-dimensional right kernel maps each candidate state in slots 0 and 1 to a projective signature. On this frozen panel, every eligible signature has a finite ratio `r` in `GF(2^41)`; all exceptional zero and infinity charts are absent.

For each edge-code family `c`, construct the monic quartic `F_c(Z)=∏_(s in c)(Z+r_s)`. Two families can share a quotient signature exactly when their quartics have a common root, equivalently when `Res(F_a,F_b)=∏_(s in b)F_a(r_s)=0`. The public target enters the quotient kernel before these polynomials are built. A nonzero resultant rejects every one of the 16 signed-state combinations in that family pair without testing any of them individually. The runner checks the column rule and exact signature equality only for compatible families.

| Stage | Frozen N41 result |
| --- | ---: |
| Eligible states / code families per free slot | 144 / 36 |
| Signed states per family | 4 |
| Family pairs tested | 1,296 |
| Nonzero resultants, whole family pairs rejected | **1,295** |
| Compatible family pairs | **1**, codes `(6,196)` |
| Signed-state combinations after family filter | 16 of 20,736 |
| Exact compatible state pairs | **1**, `(12,122)` |
| Families with full two-dimensional linear span | 36 / 36 in each slot |
| Runner interval / monitored parent wall | 0.329 s / 1.024 s |
| Sampled peak combined RSS | 49,119,232 B |

The monitored parent used one checked-Sage-launched worker, a frozen 30-second wall cap, and 4-GiB RSS cap. The 0.329-second runner interval includes quotient construction, all family polynomial construction, and all resultant tests. The 1.024-second parent interval additionally includes the checked launcher and process startup. Both are ordinary-host diagnostics. The prior root-hash quotient joined the same 144-by-144 panel in 0.158 seconds on an earlier ordinary-host run; these are not matched isolated timings. In operation count, this pairwise resultant makes 1,296 quartic-family tests while the root hash performs two linear passes, so this implementation does not improve the fixed-suffix terminal join.

The four fixed suffix states are part of the retrospective correctness panel. [verify.py](verify.py) independently rebuilds the root keys, checks every frozen quartic at its four roots, recomputes all 1,296 family compatibilities by set intersection, and binds the earlier checked-Sage group subtraction over all 20,736 state pairs. [verification.json](verification.json) records the passing readback. The experiment is a stage-level design with `candidate_id: null`.

## Transfer test and next design

The independently audited W23 N131 source has 1,049,218 edge-code families per slot, each with four signed states. Pairwise resultants for two free slots would require **1,100,858,411,524 family pairs**, or **4,403,433,646,096 quartic evaluations**, for even one fixed four-slot suffix. The four-slot suffix itself has **310,243,646,009,125,001,216,659,456 labeled signed assignments**. [projection.json](projection.json) binds these integer counts to the independent W23 census. Direct family-pair testing therefore does not approach the one-worker, 600-second, 4-GiB N131 gate. Root hashing is the appropriate terminal operator once a suffix is known.

The surviving research direction is to **keep the quartic family equations symbolic while at least one suffix family remains free**, and eliminate that family jointly with the public-target quotient. The next N41 test should unfix one suffix slot, freeze its complete family domain, and measure whether a resultant or subresultant can reject whole three-family combinations before any signed-state expansion. Its output must retain the archived relation and be checked against independent group addition. A useful N131 projection must include the work of generating or eliminating the remaining suffix families; the terminal two-slot reduction alone is insufficient.
