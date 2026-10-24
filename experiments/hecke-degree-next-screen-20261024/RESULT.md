# Degree-29 modular fibers reach one residual inverse pair

**Contribution.** A target-directed modular-polynomial screen of the 40 defined (j)-values in the eight residual old orbit columns found two degree-29 source fibers whose 30 modular roots are all rational and whose roots include residual orbit indices 1015 and 1016. The corresponding source points are ((13138,17262)) at (j=11535) and ((7159,18790)) at (j=14826). Degree 31 has no fully split source fiber among the 45 source (j)-values adjacent to the residual set.

| Degree | Candidate source (j)-values adjacent to residual set | Fully split candidate (j)-values | Source points | Residual orbit indices reached |
| --- | ---: | ---: | ---: | --- |
| 29 | 32 | 2 | 2 | 1015, 1016 |
| 31 | 45 | 0 | 0 | none |

The [protocol](protocol.json) fixes all 19,745 saved source points and the five translates of each of the eight residual orbit representatives. For each target (j), the [producer](produce.py) obtains the rational roots of (Phi_\ell(j,Y)), intersects those roots with the saved source (j)-set, then counts rational roots with multiplicity in (Phi_\ell(j_{\rm source},Y)). Symmetry of the classical modular polynomial makes this a complete search for direct (j)-adjacencies to this residual set at degrees 29 and 31. The [independent replay](validation.json) reconstructs the target point map and both modular polynomials, verifies all reverse roots, and rechecks the full-splitting count at every candidate source.

Full splitting is the necessary rationality condition for a row whose every Hecke neighbor is individually defined over \(\mathbf F_{20023}\). The two selected degree-29 points have been frozen in the [point-level protocol](l29_protocol.json) for correspondence-function construction, neighbor reconstruction, group-sum checking, and exact induced-rank measurement. This screen alone is a relation-stage diagnostic with `candidate_id: null` and `timing_claim: null`.
