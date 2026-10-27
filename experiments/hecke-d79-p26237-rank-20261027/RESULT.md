# Projection permits triples, while four-term families add complementary rank at p26237

The frozen conductor-four class at `p=26237` has 40 points with order-five residues 0:20 and 1:20. Its degree-13 neighbor polynomials all have the predicted simple factor pattern `(1)(1)(6)(6)`. Each of the 40 Hecke sources has two outside-class Frobenius traces; their aggregate sums have residues 0:20 and 2:20. This mixed projection permits three-term cancellation: **12,160 of 39,520** signed distinct-index triple patterns have zero order-five projection. The exact uniform-in-coset reference mean is `320/137 ≈ 2.34` identity triples. The actual direct and outside-trace censuses each record zero triples. Thus the observed zero is a finite incidence result, not a deterministic consequence of the order-five projection.

The projection count has a short combinatorial proof. A projected signed triple can vanish only when all three points have residue zero, giving `4·C(20,3)=4560` sign patterns, or when one has residue zero and two have residue one with opposite signs, giving `2·20·C(20,2)=7600`. Their sum is 12,160. At support four, the eligible patterns split into four zero-residue points, two zero and two unit-residue points, or four unit-residue points, yielding `8·C(20,4)+4·C(20,2)²+3·C(20,4)=197695`. The exact enumeration and Lean residue characterization check these components; the full index-counting bridge remains open in Lean.

At support four, the direct and degree-13 trace relation families again provide complementary rank:

| Row system | Verified support-four relations | Rank over F137 | Rank over Q |
|---|---:|---:|---:|
| Degree-2/5 base | 20 rows | 20 | 20 |
| Base + direct | 214 | 35 | 35 |
| Base + degree-13 trace | 209 | 35 | 35 |
| Base + both | 423 | **39** | **40** |

Each separate arm contributes four F137 dimensions beyond the other. Over Q each contributes five. A separate checked-Sage subgroup audit constructs the order-137 group from a projected class point, computes the 40 nonzero class-point logs and verifies that they annihilate all 20 base, 214 direct and 209 trace rows. This is a curve-derived witness for the F137 rank ceiling. An invertible 40-minor modulo 3 supplies the full-rank rational lower certificate.

## Frozen inputs and checks

`inputs.json` fixes the class receipt and source SHA-256, exact curve and group, factor prediction, support cap and projection-conditioned reference counts. `projection-null.json` replays all signed residue patterns and checks the exact eligible counts and rational means before the degree-13 producer. `result.json` retains every class point, base row, degree-13 factor, orbit trace, modular-polynomial check, status and phase time. `post_inputs.json` binds that receipt by SHA-256 before the support-four census. Each 40-source arm traversed 772,240 signed patterns in three alternating repetitions, retaining every relation and rank path.

The independent checked-Sage audit passed: it reconstructed 10/10/20 class strata from conductor-1/2/4 Hilbert class polynomials, refactored all 40 degree-13 polynomials, replayed every saved relation, and recomputed ranks over Q and F137. Its class-completeness check is relative to those ring-class strata. The separate order-137 log audit passed. The pinned Lean build passed the mixed-residue theorem and exact numerical kernel/minor certificates, with axiom printouts retained. The proof map keeps the full projection-count enumeration, general rank implication, and curve-specific formal bridges open.

The checked-Sage producer measured 33.75 s for function construction and 1.208 s for the degree-13 fibers on this local host. The direct support-four enumerations took 1.686–1.822 s; the outside-trace enumerations took 6.514–6.966 s. These are exploratory stage diagnostics with different preparation requirements, not a calibrated online IC comparison. `candidate_id` and `target_online_ms` remain null.

Across the three frozen larger-q follow-ups, both antipodal and mixed order-five projection patterns have a support-four path to combined rank 39 modulo the largest subgroup prime and 40 over Q. The separate-arm rank varies: `p14957` reaches the combined rank from either arm, whereas `p36037` and `p26237` require both at the declared support cap. The next experiment should test whether the relation-family overlap is predicted by more than order-five residue balance, using a prespecified broader panel rather than selecting further cases after seeing ranks.
