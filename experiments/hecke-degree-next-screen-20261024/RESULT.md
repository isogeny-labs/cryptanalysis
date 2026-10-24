# Degree-29 Hecke fibers yield two verified rows but preserve the old-column rank

**Contribution.** A target-directed modular-polynomial screen of the 40 defined (j)-values in the eight residual old orbit columns found two degree-29 source fibers. Both lift to verified 30-neighbor Hecke rows. These rows add two orbit columns and raise the sign-augmented matrix rank from 3,951 to 3,953, but the new-column projection rank also rises from 4 to 6. The induced rank on the original 3,949 orbit columns remains **3,947**, and the anchored kernel remains dimension **2**. Thus this degree-29 route reaches the residual pair but does not reduce the generic seed-log count.

| Matrix | After degree 23: rank / new projection / induced old rank | After degree 29: rank / new projection / induced old rank | Anchored kernel after degree 29 |
| --- | --- | --- | ---: |
| Hecke rows | 3,949 / 4 / 3,945 | **3,951 / 6 / 3,945** | 4 |
| Hecke and inversion rows | 3,951 / 4 / 3,947 | **3,953 / 6 / 3,947** | 2 |

The source points are ((13138,17262)) at (j=11535) and ((7159,18790)) at (j=14826). They are inverses modulo 5-torsion translation, and (a_{29}=0). Both reconstructed fibers have 30 rational (x)-roots and 30 verified neighbors. The [point-level result](l29_result.json) saves all 60 neighbors, two rows, two new orbit representatives, and the rank diagnostics. The [independent validator](l29_validation.json) rebuilt the neighbors from saved functions, checked the group sums using separate integer affine arithmetic, and reproduced ranks 3,951 and 3,953 over the integers with six projected new columns.

| Degree | Candidate source (j)-values adjacent to residual set | Fully split candidate (j)-values | Source points | Residual orbit indices reached |
| --- | ---: | ---: | ---: | --- |
| 29 | 32 | 2 | 2 | 1015, 1016 |
| 31 | 45 | 0 | 0 | none |

The [protocol](protocol.json) fixes all 19,745 saved source points and the five translates of each of the eight residual orbit representatives. For each target (j), the [producer](produce.py) obtains the rational roots of (Phi_\ell(j,Y)), intersects those roots with the saved source (j)-set, then counts rational roots with multiplicity in (Phi_\ell(j_{\rm source},Y)). Symmetry of the classical modular polynomial makes this a complete search for direct (j)-adjacencies to this residual set at degrees 29 and 31. The [independent replay](validation.json) reconstructs the target point map and both modular polynomials, verifies all reverse roots, and rechecks the full-splitting count at every candidate source.

Full splitting is the necessary rationality condition for a row whose every Hecke neighbor is individually defined over \(\mathbf F_{20023}\). The two degree-29 points were frozen in the [point-level protocol](l29_protocol.json) before the 29 correspondence functions were built from (q)-series. The [saved functions](l29_functions.json) and [runtime receipt](sage_runtime.json) permit replay. Degree 31 has no fully split source fiber among the 45 source (j)-values adjacent to the residual set.

The [point-lift control](l29_lift_result.json) applies the saved (j)-map to each modular root. Each source has 29 distinct rational modular roots with total multiplicity 30; every distinct root has exactly one rational point lift on (X_0(11)). [Direct enumeration](l29_lift_validation.json) over all 20,105 rational curve points reproduces those lift counts. This is a relation-stage result with `candidate_id: null` and `timing_claim: null`; it supplies no new single-target online comparison. The next structural step is a relation family whose rows impose constraints on the old orbit columns after new neighbors are eliminated, such as a correspondence with shared new-column support across more than two fibers.
