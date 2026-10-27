# Two short trace cancellations complete the order-5 class relation space

Two exact degree-13 row differences raise the frozen D=-79, conductor-2 class matrix from **rank 17 to rank 19 over F_5**. The final rank also equals 19 over Q. A checked-Sage replay confirms that the F_5 right kernel is one-dimensional and equals the independently computed five-primary projection of the 20 class points. This reaches the 19-dimensional relation-space ceiling for this fixed 20-point, order-5 class.

| Matrix | Rank over Q | Rank over F_5 |
| --- | ---: | ---: |
| Corrected degree-2 rows | 10 | 10 |
| Plus prior degree-5 orbit rows | 16 | 16 |
| Plus individually closed degree-13 rows | 17 | 17 |
| Plus degree-13 source 13 minus source 15 | 18 | 18 |
| Plus degree-13 source 14 minus source 16 | 19 | 19 |

The selected source pairs share their outside trace points exactly: sources 13 and 15 both trace to `(48,59)`, and sources 14 and 16 both trace to `(74,9)`. Subtracting each pair removes that auxiliary point. The resulting integer class relations are:

```text
-P_12 - 5P_13 + P_14 + 5P_15 = 0,
-P_5 + P_7 + P_13 - 4P_14 + 4P_16 - P_17 = 0.
```

The [protocol](PROTOCOL.md) fixed the 29 expanded rows, coefficients `±1`, support cap three, canonical sign/order, and F_5 rank-selection gate before output. The complete search retained **13 valid support-two** and **158 valid support-three** group-law cancellations. The two displayed rows are the first rank-increasing candidates; all 171 candidates, their supports, exact integer rows, and the rank path are in [result.json](result.json). Candidate generation uses only point addition and equality on the saved outside traces, with no auxiliary scalar-log lookup.

The [independent checked-Sage validator](verify.py) reconstructs all 29 expanded equations from the pinned degree-5 and degree-13 orbit receipts, independently enumerates all supports and signs, checks every auxiliary group cancellation and class row, and replays Q/F_5 ranks. It then multiplies each class point by the cofactor 18: ten points have a nonzero order-5 component, and the saved matrix kernel is exactly the span of that projection vector. [validation.json](validation.json) and the [checked runtime](sage-runtime-info.txt) retain this control. The validator returned `SHORT_TRACE_RELATIONS_PASS candidates 171 selected 2 rank_mod5 17 -> 19 kernel_dimension 1`.

The pinned Lean module [formal/ShortTrace.lean](formal/ShortTrace.lean) checks the two 21-coordinate outside-column cancellations, a nonzero vector annihilating all 27 final rows, and an explicit 19-by-19 minor with a displayed inverse modulo 5. The [proof map](formal/PROOF_MAP.json) and [build check](formal/CHECK.md) record the standard rank implications used in the written argument and the remaining finite-field formalization boundary. The Lean build passed; `#print axioms` lists only standard `propext` where present.

This is a complete relation-space result for the fixed order-5 class. The next experiment is to freeze a target-dependent handling rule and an anchor-log source, then measure a verified one-target interval against same-point rho under the repository's candidate and benchmark contracts. A larger class would test whether the short auxiliary-trace closure remains useful when the subgroup and trace graph grow.

Reproduce from the repository root:

```sh
python3 experiments/hecke-trace-short-relations-20261027/run.py
./sage --runtime-info > experiments/hecke-trace-short-relations-20261027/sage-runtime-info.txt
./sage -python experiments/hecke-trace-short-relations-20261027/verify.py
cd experiments/hecke-trace-short-relations-20261027/formal
python3 generate.py
lake build ShortTrace
```
