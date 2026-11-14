# Alternative gluing proof map

2026-11-13. All standing unsigned. Native f33c42/7c9bf4 and written5f7e4c
are distinct from the exact local Lean checks below. Both unchanged original
gates (producer4.35,consumer4.34.1) audit8 model plus3 chain declarations,
zero trusted; no holes, custom axioms or native evaluation. [pcc:unverified]

| Mathematical obligation | Exact Lean declaration | Local binding / scope |
| --- | --- | --- |
| Translate source at actual2-root | GluingModels223.translated_source_cubic | bdeb78; universal cubic identity |
| Diagonal entries from Delta | GluingModels223.adjugate_diagonal_from_Delta | 8b9fee; exact product-equation hypothesis |
| det(adj(H))=det(H)^2 | GluingModels223.symmetric_adjugate_determinant | e63dbc; universal symmetric-matrix polynomial |
| adj(adj(H)) off-diagonal | GluingModels223.symmetric_adjugate_cofactor | 6a6967; universal cofactor identity |
| Pair smoothness discriminant | GluingModels223.symmetric_adjugate_pair_discriminant | 408de8; universal polynomial |
| Even-quartic Jacobian discriminant | GluingModels223.even_quartic_discriminant | fcb523; universal coefficient identity |
| Explicit coordinate residual | GluingModels223.even_quartic_map_residual | df1c13; s²=alpha hypothesis |
| Coordinate image on Jacobian model | GluingModels223.even_quartic_map_on_jacobian | 02dc7d; actual square/on-curve equations |
| Both chained compositions[4] | GluingChain223.two_dual_pairs_give_both_four | eb286e; both original/new[2] pair hypotheses |
| Odd-domain pullback injectivity | GluingChain223.pullback_injective_from_actual_double_inverse | 7424e9; actual doubling left inverse required |
| Polarized product degree column | GluingChain223.polarized_product_degree_one_column | 47c63e; nonnegative integer degrees summing1 |

Model polynomial identities and the degree lemma use standard propext,
Classical.choice and Quot.sound. The two functional implications use no
axioms. Whole original proof captures are7f5b3a/04f04b (models) and
098831/872aee (chain), every member and raw/archive digest retained.
Original PCC bindings and canonical declaration digests are in the two
evidence/gluing-*-bindings-01 directories. [pcc:unverified]

Still written/open in Lean: actual abelian/Jacobian/Picard definitions,
HLP's kernel identification, extension of the birational genus1 map,
auxiliary-sign translation, all scheme-ideal/trace/reducer bridges, global
V4/cross-homomorphism identities, Frobenius descent, polarizations and
degree functoriality, actual odd-subgroup doubling inverse, theta/torsion
bridge and finite native execution. The abstract implications do not
replace these hypotheses or establish signed execution. [pcc:unverified]

Written endpoint argument uses the old unique rational2-kernel and the
actual distinct nonexceptional elliptic j conjugates. Polarized product
automorphisms act trivially on A[2]; the literal original model identifies
its old gluing kernel. Three other square masks differ, so their targets
are not F223-ppav-isomorphic to old J. This remains a written geometric
argument with unsigned computed premises, not a fully formal theorem.
Mutual new-target/geometric-extension isomorphisms and full cost remain
unasserted. [pcc:unverified]
