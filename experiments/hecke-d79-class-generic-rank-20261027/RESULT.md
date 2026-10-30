# Direct class-point triples span the D79 p317 q-primary relation kernel

Exhaustive signed relations of support at most three among the **39 frozen class points** produce **122 verified rows**. Their rank is **38 over F61**, the full kernel dimension allowed by the nonzero q-primary class-point coordinate vector. With the same 18-row baseline, a greedy 20-row subset reaches that rank. The complete direct row set has rank **39 over Q**, certified independently by a 39×39 minor modulo 2. Thus, at this finite class geometry, direct point triples already supply the q-primary rank reached by the earlier Hecke trace-cancellation rows.

| Relation source | Verified candidate rows | F61 rank alone | F61 rank with 18 base rows | Q rank with 18 base rows |
| --- | ---: | ---: | ---: | ---: |
| Direct signed class-point support ≤3 | 122 (all support 3) | 38 | 38 | 39 |
| Hecke: 5 class-closed rows plus 80 short cancellations | 85 | — | 38 | 39 |

The five Hecke class-closed rows raise the baseline rank from 18 to 23. The earlier greedily selected 15 short-cancellation rows then raise it to 38 over F61; the present direct enumeration needs 20 selected rows from the 18-row baseline. These selected-row counts are **not** a cost comparison: the candidate sets, row sparsity, and generation methods differ. All 122 direct rows, candidate order, selected indices, and complete rank path are in [result.json](result.json).

The [protocol](PROTOCOL.md) fixed the class/search receipt hashes, signs, enumeration order, rank fields and validation route before output. The pure-Python [producer](run.py) checked exact point sums and the frozen q-primary coordinate dot product. [Independent checked-Sage replay](verify_sage.py) rebuilt `E11a1(F317)` with order 305, re-enumerated every signed support-one/two/three candidate, and recalculated all ranks with Sage matrices. It matched the complete candidate list and selected path; [validation.json](validation.json) records `PASS`, with the [Sage runtime receipt](sage-runtime-info.txt).

## Rank argument and formalization

Let `R` be the matrix of the 18 baseline rows and all 122 direct rows, with 39 columns ordered as the frozen class points. The nonzero q-primary coordinate vector `v` in the frozen search receipt satisfies `Rv=0` over F61, as each signed row is an exact point relation. Therefore `rank_F61(R) ≤ 38`. The selected 38 rows admit an explicit 38×38 column minor with inverse modulo 61, so `rank_F61(R) ≥ 38`. Separately, 39 direct rows admit an explicit 39×39 inverse modulo 2. Their integer determinant is odd and hence nonzero, giving rank 39 over Q.

The pinned Lean [certificate module](formal/DirectRankP317.lean) checks all 140 row-dot products, nonzero `v`, and the inverse identities for both minors; its `#print axioms` audit reports only standard `propext` for the finite inverse identities. The finite-matrix rank implications and the bridge from the numerical point coordinates to the abstract matrix are written above and identified as remaining formal obligations in the [proof map](formal/PROOF_MAP.json). The certificates provide exact, reproducible arithmetic evidence without substituting an assumed rank statement.

This is a relation-stage control on one frozen class, with `candidate_id: null` and `target_online_ms: null`. A next experiment should measure **source generation and verified rank per unit cost** for direct triples and Hecke rows under one frozen resource envelope, then test the same comparison on a larger unseen class where direct triple yield may change.

Reproduce from the repository root:

```sh
gtimeout 120 python3 experiments/hecke-d79-class-generic-rank-20261027/run.py
./sage --runtime-info > experiments/hecke-d79-class-generic-rank-20261027/sage-runtime-info.txt
gtimeout 180 ./sage -python experiments/hecke-d79-class-generic-rank-20261027/verify_sage.py
python3 experiments/hecke-d79-class-generic-rank-20261027/formal/generate.py
cd experiments/hecke-d79-class-generic-rank-20261027/formal
lake build DirectRankP317
```
