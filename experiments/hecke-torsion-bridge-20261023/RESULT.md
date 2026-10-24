# Torsion translation reaches new trace strata but adds no old-class constraint

**Contribution.** Translating the 120-point $D=-227$ class on $X_0(11)$ by the rational point $T=(5,5)$ of order 5 reaches 234 new source points. Forty of their degree-2 or degree-3 Hecke rows have fully rational, verified neighbors, and every accepted source has an absolute Frobenius trace different from the base class's 200. After identifying points that differ by $T$, these rows raise total rational rank from **60 to 100**, but they introduce 128 new orbit columns. Their new-column projection has rank **40**, so elimination leaves the original 117 orbit columns at rank **60**: the induced increment is **zero**.

| Gate | Exact result |
| --- | ---: |
| Base class points / old $T$-orbits | $120 / 117$ |
| New sources in the $\pm T$ layer | $234$ |
| Fully rational verified new rows, degree 2 / 3 | $24 / 16$ |
| New orbit columns | $128$ |
| Rank of base rows on old orbit columns | $60$ |
| Rank of all base and new rows | $100$ |
| Rank of all rows projected onto new columns | $40$ |
| Induced rank on old columns after eliminating new columns | $100-40=60$ |
| New independent old-only constraints | **0** |

The [protocol](protocol.json) fixed the committed $D=-227$, $p=12043$ matrix, the checked $X_0(11)$ model, $T=(5,5)$, translations by $\pm T$, degrees $2$ and $3$, the rational-neighbor gate, and the induced-rank calculation before production. The producer checks $5T=0$, builds each unique translated source, verifies every accepted Hecke neighbor against the modular polynomial and group-sum identity, and saves all source statuses and sparse rows in [result.json](result.json). Of the 468 source-degree attempts, 40 passed the all-rational gate and 428 did not. No row with unresolved neighbors was silently added. The [Sage runtime receipt](sage_runtime.json) was saved before that job.

The zero increment has a direct combinatorial certificate. Each of the 40 new rows contains at least one **private new column with coefficient 1**: that column occurs in no other new row and in no base row. The [private-column witness](private_witness.json) names one such orbit column for every row; 124 of the 128 new columns occur in just one new row. Any linear combination of new rows whose new-column part vanishes must therefore give coefficient zero to each new row. The old-only row space remains the base row space. The [Lean theorem](formal/PrivateNewColumns.lean) proves this structural implication for additive maps when the new-column projection is injective. Its [build receipt](formal/build.json) records a successful pinned build and `#print axioms` of `propext` and `Quot.sound`; the exact private-column matrix-to-Lean bridge is checked computationally and remains a formalization step.

The [independent integer-curve validator](validate.py) reconstructs point addition for $y^2+y=x^3-x^2-10x-20$ modulo 12043, checks $T$ and all saved points, translates the 120 frozen points again, rebuilds every base and new quotient row, verifies the private witnesses, and computes all three ranks over $\mathbb Q$ and two finite fields. Its [receipt](validation.json) is `PASS_TORSION_BRIDGE_ZERO_INDUCED_RANK_CERTIFIED`. A separate [checked-Sage replay](validate_trace.py), with its own [runtime receipt](sage_runtime_validator.json), recomputes every translated source's $j$-invariant and trace and all 40 modular-neighbor and group-sum checks; its [receipt](trace_validation.json) confirms 40 accepted rows outside the base absolute-trace stratum. The [proof map](PROOF_MAP.json) distinguishes the checked structural theorem from the computational instance bridge.

The experiment tests one $\pm T$ translation layer at one frozen field. It gives a concrete cross-trace connection, but this layer's Hecke rows each carry a private new unknown and therefore do not improve the original class's relation rank. The next gate is a second layer or a closed collection of translated Hecke rows in which new columns recur enough to cancel; the same induced-rank calculation must be used before treating any total-rank growth as progress on the original class. This remains a relation-stage study with `candidate_id: null` and `timing_claim: null`.
