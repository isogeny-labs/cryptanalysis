# Frozen Fricke eigenspace rank test

Use the exact 768-column, 576-row `D_K=-2631, f=6, p=23743` matrix from
PR #1193, the independently audited floor witness vectors, and the 768-point
permutation from PR #1194. Pin all three input hashes before calculation.
Require the saved permutation to be a fixed-point-free involution, each
relation row to transport to its recorded partner, and every floor witness
to transport into the witness span. The global identification of the
permutation with `W_11` is the theorem in PR #1195.

For each point pair `{i,W(i)}`, choose the lower column index `i` and map a
row `r` to coordinates `r_i+r_W(i)` and `r_i-r_W(i)`. Compute exact rational
ranks of both projected relation matrices and both projected floor-witness
matrices. Repeat the rank calculation modulo 23 and 1000000007 as an
independent arithmetic cross-check. Confirm that the two rational projected
ranks sum to the previously certified full rank 480, and that the floor
projected ranks sum to 54. Preserve unequal ranks if found. Record the
column-pair count, row-pair count, projected nullities, and whether Fricke
alone closes the rank gap. No wall-time or candidate speedup is inferred.
