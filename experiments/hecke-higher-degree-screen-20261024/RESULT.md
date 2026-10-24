# Modular-polynomial splitting isolates two degree-23 routes to the residual component

**Contribution.** A complete modular-polynomial screen of all 19,745 saved p=20023 source points reduces the next Hecke construction to **two degree-23 (j)-adjacencies** that could touch the residual 14-orbit component. Degree 19 has 16 source points whose modular polynomial splits completely, but none of their rational (j)-neighbors matches an ambiguous orbit's (j). Degree 23 has six completely split source points, and two source (j)-values have one (j)-neighbor each in that residual set: (4643\to18217) and (19989\to14962).

| Degree | Distinct source (j) values with full splitting | Source points represented | Full-splitting sources in the ambiguous orbits | (j)-adjacencies to ambiguous orbits |
| --- | ---: | ---: | ---: | ---: |
| 19 | 8 | 16 | 0 | 0 |
| 23 | 3 | 6 | 0 | **2** |

The [protocol](protocol.json) froze all five torsion translates of every one of the 3,949 reachable orbit representatives. The [producer](produce.py) computed (j) for each point, grouped the 19,743 defined-(j) sources into 11,619 distinct values, and counted rational roots of Φ₁₉ and Φ₂₃ with multiplicity. Two source points have undefined (j). The [independent validator](validation.json) rebuilt the (j)-map and both modular polynomials, reproduced every saved root count and source weight, and checked the fully split (j)-values against all 70 translates of the 14 ambiguous orbits. The [runtime receipt](sage_runtime.json) identifies the checked Sage build.

Complete rationality of every degree-ℓ Hecke neighbor implies that all ℓ+1 associated (j)-values are rational; hence Φℓ((j(P),Y)) must split completely. This makes the screen a necessary-condition filter. A completely split modular polynomial does not by itself identify the correct points of (X_0(11)), verify their field of definition, or produce a group-sum relation. The two degree-23 adjacencies are therefore precise inputs for a targeted Hecke-function reconstruction, not accepted relation rows. The [proof map](PROOF_MAP.json) records the finite audit and the remaining formal bridge.

This is a relation-stage diagnostic with `candidate_id: null` and `timing_claim: null`. The next run should build degree-23 Hecke functions only once, reconstruct neighbors for the six full-splitting source points, and measure the induced rank on the old 3,949-column boundary after any new columns are eliminated.
