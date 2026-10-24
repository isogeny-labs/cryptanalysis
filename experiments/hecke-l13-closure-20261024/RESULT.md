# Degree-13 Hecke rows add two columns without closing the old kernel

**Contribution.** At (p=20023), degree 13 yields **10 verified rational Hecke rows** from the 19,745 saved torsion-quotient source points. They introduce two new orbit columns. The anchored GF(4021) rank rises from 3,943 to 3,945, exactly matching rank two on the new-column projection, so induced rank on the original 3,949 columns remains 3,943. None of the 10 rows touches the 14 ambiguous old columns. An independent integer-curve replay gives exact full rank 3,945 and exact induced old rank 3,943.

| Source status | Count |
| --- | ---: |
| Trace obstruction | 16,551 |
| Eligible, fewer than 14 rational roots | 3,182 |
| All 14 roots rational; group sum and modular incidence verified | 10 |
| Undefined source (j) | 2 |

The [protocol](protocol.json) froze the source set, the trace sieve, the degree-13 acceptance rule, and the old-column kernel comparison before production. The sieve retains every source with (j=0) or (1728), and otherwise requires the absolute Frobenius trace to be 5 or 8 modulo 13. If Frobenius acts as a scalar (s) on 13-torsion, its determinant is (p\equiv3\pmod{13}), so (s\equiv4) or (9) and (2s\equiv8) or (5). The [Lean theorem](formal/TraceSieve.lean) checks that finite arithmetic without axioms. The [direct sieve audit](sieve_audit.json) evaluated the neighbor polynomial for **all 16,551 screened-out sources** and found zero fully rational cases, independently covering exceptional behavior in the finite experiment.

The [finite-field q-series builder](modular_hecke.py) identified the 28 degree-13 Hecke functions at precision (q^{5136}). Its [control](smoke.json) reproduced every rational-function coefficient modulo 20,023 at degrees 2, 3, and 5. The [saved functions](functions.json) are hashed by the [result](result.json). For each accepted degree-13 row, the producer checked all 14 rational neighbors, Φ₁₃ incidence, and the point-sum identity (\sum Q_i=4P); the independent [validator](validation.json) repeated the source classification, reconstructed all 10 point sums using separate integer arithmetic, and recomputed the exact induced rank. The [runtime receipt](sage_runtime.json) identifies the checked Sage build. The [proof map](PROOF_MAP.json) separates the Lean residue lemma from the externally replayed modular and matrix certificates.

The accepted rows all arise from absolute trace 18 and touch 132 orbit columns, including the two new inverse-pair columns. Their old-column information is already in the prior row span after the new columns are eliminated. This is a relation-stage result with `candidate_id: null` and `timing_claim: null`; larger Hecke degrees should be selected against the residual component's traces before incurring their q-series and incidence costs.
