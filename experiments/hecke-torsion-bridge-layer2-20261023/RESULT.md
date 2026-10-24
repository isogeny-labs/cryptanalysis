# A second torsion–Hecke frontier adds rows but leaves prior constraints unchanged

**Contribution.** Exhausting all five torsion representatives of the **128 new orbit columns** from the first $D=-227$ translation layer yields 640 candidate sources and **166 verified Hecke rows**. Those rows add exactly **166** to total rational rank, bringing the 276-row system to rank **266**. They also introduce **412** further orbit columns, and their projection onto those brand-new columns has full row rank **166**. After eliminating all columns beyond the original class, the induced rational rank remains **60**; after eliminating only the second-layer columns, the first-layer induced rank remains **100**. The second layer therefore contributes zero constraints to either earlier column set.

| Rank boundary over $\mathbb Q$ | Before layer 2 | After layer 2 | Induced increment |
| --- | ---: | ---: | ---: |
| Total relation rank | 100 | **266** | 166 |
| Rank induced on original 117 torsion-orbit columns | 60 | **60** | **0** |
| Rank induced on all first-layer 245 columns | 100 | **100** | **0** |
| Projection rank onto 412 second-layer columns | 0 | **166** | 166 |

The [frozen protocol](protocol.json) selected every one of the five $T=(5,5)$ representatives for each first-layer new orbit, with no adaptive filtering by outcome. The [producer](produce.py) checked degrees 2 and 3 at all 640 sources: 112 degree-2 and 54 degree-3 rows passed the all-rational neighbor, modular-polynomial, and group-sum gates. The other 1,114 source-degree attempts retained their non-rational status. A separate [checked-Sage replay](validate_trace.py) verified every source $j$-invariant and trace and all 166 accepted modular-neighbor identities; every accepted source has absolute trace different from the original class's 200. The run and replay each saved a checked Sage runtime receipt.

The [result](result.json) preserves all source statuses, accepted sparse rows, old and new orbit-column partitions, and both finite-field rank calculations. The independent [integer-curve audit](validate.py) reconstructs all 640 source points and every saved row from group arithmetic, then recomputes exact rational ranks and ranks modulo 101 and 1,000,000,007. Its [receipt](validation.json) is `PASS_TORSION_LAYER2_ZERO_INDUCED_RANK_CERTIFIED`.

Of the 166 new rows, **162** each have a private brand-new column. The remaining four are also independent on the new columns: the [projection certificate](projection_certificate.json) selects 166 new-column pivots modulo 101 and verifies that the resulting $166\times166$ submatrix has rank 166 over $\mathbb Q$. Consequently no nonzero combination of second-layer rows can have zero second-layer projection. The exact identity

`induced rank on retained columns = rank(all columns) − rank(discarded-column projection)`

then gives $266-166=100$ for the first-layer columns and $266-206=60$ for the original columns. The [proof map](PROOF_MAP.json) applies the previously built Lean theorem `PrivateNewColumns.oldOnly_eq_original` to this new injective projection; the finite matrix pivot certificate establishes its instance hypothesis computationally. A full Lean construction of the finite-field Hecke incidence remains open.

Two layers show that cross-trace Hecke rows can be plentiful while each frontier still pays for independent new columns. The next decisive experiment is the third frontier, where the new-column pool approaches the finite torsion quotient and collisions may finally create a closed row combination. It must use the same induced-rank gate, retaining all source and failure statuses. This is a relation-stage result with `candidate_id: null` and `timing_claim: null`.
