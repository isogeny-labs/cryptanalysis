# Conductor-42 one-row augmentation

Use the exact recovered row in `diagnostic.json`, provided every diagnostic
gate passed. Append it once to the 129 archived rows. Require the Fricke
transform of every augmented row to appear with the same multiplicity in
the augmented row multiset. Compute the augmented full rank and `+/-`
projected ranks over `QQ`, `F_23`, and `F_1000000007`. The prespecified
expectation from the original panel is full rank 104 and split `52/52`;
retain a mismatch. The diagnostic protocol already fixed the source row,
partner, root multiplicities, modular identity, and group identity before
this calculation.
