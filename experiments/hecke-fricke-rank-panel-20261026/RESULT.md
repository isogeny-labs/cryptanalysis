# Four conductor classes have balanced Fricke relation ranks

The Fricke `+` and `−` relation ranks are equal in four frozen
`D_K=-7` Hecke matrices whose conductor and degree support vary. At
conductor 42, the archived collector omitted one complete degree-7 fiber
because two neighbors share an x-coordinate. Reconstructing that partner
from the global Fricke action restores row closure without changing the
matrix rank. The resulting 130 rows give `52/52` ranks.

| Reached conductor | Hecke degrees | Points | Complete rows after repair | Fricke `+` rank | Fricke `−` rank | Full rank |
| ---: | --- | ---: | ---: | ---: | ---: | ---: |
| 42 | 2, 3, 7 | 160 | 130 | 52 | 52 | 104 |
| 70 | 2, 5, 7 | 224 | 170 | 70 | 70 | 140 |
| 150 | 2, 3, 5 | 740 | 656 | 250 | 250 | 500 |
| 210 | 2, 3, 5, 7 | 1120 | 1082 | 392 | 392 | 784 |

The [frozen panel protocol](PROTOCOL.md) specified the four saved matrices,
their hashes, and the equal-rank prediction. The [initial panel](result.json)
found point closure in all four cases and row closure in three. At
conductor 42 it recorded one missing transformed row and left its
eigenspace ranks null as planned. The [diagnostic protocol](DIAGNOSTIC_PROTOCOL.md)
then fixed source row 74, source column 88, and partner column 67 before
reconstruction. The source degree-7 polynomial has eight simple rational
x-roots; the partner has seven distinct rational x-roots, one of
multiplicity two. The old `neighbours_all` routine requires eight distinct
x-roots and therefore rejects the partner.

The [diagnostic result](diagnostic.json) reconstructs all eight partner
points by `W_11(P)=T-P`. Their x-multiset equals the target polynomial's
root multiset with multiplicity; every source and partner j-pair satisfies
the classical degree-7 modular polynomial; and the group sum equals
`a_7 W_11(P)`. The recovered integer row exactly matches the transported
archived row. Inserting it leaves rank 104 over `QQ`, `F_23`, and
`F_1000000007`. Under the [augmentation protocol](AUGMENTED_PROTOCOL.md),
the completed row multiset forms 65 Fricke pairs and has ranks `52/52`
over all three fields, as saved in [augmented.json](augmented.json).
An [independent pure-Python replay](validation.json) uses separate affine
point arithmetic modulo 3187 to reconstruct that row and a separate
sparse modular elimination to reproduce its ranks. Its first draft used
`+2` rather than `a_7=-2` in the group-sum assertion and failed; the
corrected replay passes. The checked-Sage [runtime receipt](runtime-info.json),
scripts, stdout, and stderr are retained.

**Proof map.** The global identity `W_11(P)=T-P` is proved in
[PR #1195](https://github.com/isogeny-labs/cryptanalysis/pull/1195).
For every two-point orbit, the rational coordinate change
`(x,y)↦(x+y,x-y)` is invertible; the pinned Lean theorem in
[PR #1196](https://github.com/isogeny-labs/cryptanalysis/pull/1196)
checks both inverse identities and its axiom report. The four exact
matrix ranks and degree-7 fiber identities are checked by the retained
Sage and independent integer artifacts; those full finite matrices are
not formalized in Lean. The measured balance across four cases is a
new empirical pattern, not a general rank theorem. These are
relation-stage measurements with `candidate_id: null` and
`timing_claim: null`.

The repeated-x row is a concrete collector coverage correction. A
follow-up producer should reconstruct Hecke neighbors with multiplicity
and independently validate the resulting point list before using its
matrix rank in a wider conductor search.
