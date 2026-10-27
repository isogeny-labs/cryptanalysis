# Order-five projection predicts an exact three-term obstruction in two larger-q classes

The eight-case prespecified panel finds two conductor-four classes whose 40 points project entirely into the antipodal nonzero residues of the order-five quotient. Their signed support-three relation counts are exactly zero. The first qualifying case is `p=14957`, `#E=14890`, `q=1489`; its projection has 40 points at residue 1, and the base Hecke row rank remains 20 modulo 1489 after direct rows. The second is `p=36037`, `#E=36275`, `q=1451`, with residues 1:20 and 4:20 and the same zero-yield/rank-20 outcome.

| p | #E | largest q | order-five residue counts 0,1,2,3,4 | signed triples | base rank mod q | base + direct rank mod q |
|---:|---:|---:|---|---:|---:|---:|
| 3797 | 3880 | 97 | 20,20,0,0,0 | 19 | 20 | 34 |
| 8237 | 8255 | 127 | 0,20,20,0,0 | 9 | 20 | 29 |
| 8597 | 8520 | 71 | 0,20,20,0,0 | 8 | 20 | 28 |
| 12197 | 12280 | 307 | 0,20,20,0,0 | 5 | 20 | 25 |
| 12637 | 12655 | 2531 | 0,20,20,0,0 | 3 | 20 | 23 |
| 14957 | 14890 | 1489 | 0,40,0,0,0 | 0 | 20 | 20 |
| 26237 | 26030 | 137 | 20,20,0,0,0 | 0 | 20 | 20 |
| 36037 | 36275 | 1451 | 0,20,0,0,20 | 0 | 20 | 20 |

All classes contain 40 distinct points. No signed support-one or support-two direct relation occurred in this panel. The mixed-projection `p=26237` class also yielded zero triples; hence the antipodal projection is a sufficient obstruction, while this case requires a separate explanation. The decline from 19 to 3 direct triples in the first five cases is an observed finite panel, not a fitted yield law.

`inputs.json` freezes the curve, first-eight prescreen, source digest, and caps. `class-result.json` retains points, base rows, projections, group invariants and stage times. `post_inputs.json` binds the class receipt by SHA-256. `analysis.json` records every direct relation, rank path, and exact iid reference mean. `audit.json` reports `PASS` for all eight using checked Sage, independent ring-class polynomial fibers, Sage group-law replay, and rational/mod-q matrix ranks. The audit's class completeness is relative to conductor strata 1, 2 and 4 as declared in the protocol. The local stage times are exploratory algorithmic diagnostics. `candidate_id` and `target_online_ms` are null because this is not a complete IC pipeline measurement.

The Lean theorem `CosetPanel.no_three_in_antipodal_class` proves the structural obstruction for an additive projection to `Fin 5`; the module checks all eight residue-count totals and prints its axioms. `formal/PROOF_MAP.json` records the remaining curve-specific and rank formalization obligations. The prespecified next experiment is a full degree-13 Hecke row census for `p=14957`, with class and source identity held fixed, to test whether those rows recover rank unavailable from direct triples.
