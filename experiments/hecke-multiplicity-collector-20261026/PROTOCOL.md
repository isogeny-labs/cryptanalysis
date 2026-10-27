# Frozen repeated-x collector replay

Implement a drop-in replacement for `Reduced.neighbours_all` using the
unchanged checked-Sage q-expansion functions from the archived 11a1
producer, SHA-256
`7e66144e76bf62f7e645d87cc58be2bb0f7cc5e52601665650ef0706a6f715fb`.
For repeated rational roots of the neighbor x-polynomial, solve the
Vandermonde system for the total y-coordinate at each distinct x. Enumerate
point multiplicities among the curve lifts of each x; accept a unique
multiset only if it matches every x/y power sum and the Hecke group sum.
Return an explicit status for nonrational, inconsistent, and ambiguous
fibers. Keep the original simple-root path as a direct comparison.

Replay the already frozen `D_K=-7` classes at conductors `42,70,150,210`
with degree supports `{2,3,7}`, `{2,5,7}`, `{2,3,5}`, and `{2,3,5,7}`.
Input SHA-256 values respectively are
`f4a8b964dad70fc8d697d1163f2fa8a963a44882731ae18518e1ace2951c311d`,
`efe387fe31c22001b9eeaabe72d920835f80a2300b1aaa4d151015b05d2357ef`,
`49e33851a0ed64e470f1693001664c6f76f58aea9e2e65b6974d1618dfa15e06`,
and `616c4583ac761e9eb965c9ce36b366e3a67b104b881d9eb8a8cee47f2799844e`.
Count status by degree, require all previously accepted neighbor multisets
to match, verify new rows against the classical modular polynomial, retain
the new row coordinates, and compute old/new exact rational and two modular
ranks. Preserve zero additions and any changed rank. The known conductor-42
degree-7 partner is a positive control, not a prediction for other cells.
