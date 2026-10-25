# Exact N41 target-conditioned gate: native rank versus quotient

The native direct-rank check completed the frozen four-axis N41 gate in 1.67–1.99 seconds of query traversal, versus 5.79–6.04 seconds for the normalized quotient check. Both methods checked 1,989,120 roots across 248,640 family/chart combinations, returned the same unique gate and source-product witness `(chart 0, left code 24, right code 37, root 2, third code 10)`, and recorded zero exceptional leading coefficients. The direct-rank kernel is the faster implementation on this input. These are ordinary-host stage timings with shared input and alternating order; they are not a complete IC or rho comparison.

## Reproduction and identity

`n41_quotient_native_prepare_20261025.py` checks SHA-256 for the geometry, target table, and 1,554 exact first-two-code families before writing `n41_quotient_native_input_20261025.tsv`. The frozen input SHA-256 is `05cdc6655cd2f06531755457f6fe16b8acbfc41999cf889f6a025fa17b00fd5d`. It contains a rank-seven third-product basis, 40 actual source products, 160 target charts, and eight roots per family. The C++ source SHA-256 is `85838e2a2c55655a7bb3f2325fc50da8074b1ae2367271b124fb534d5e86aebf`; the archived binary SHA-256 is `595a9010255fbdaee2f4fe1e68535fde63b6ca32b577af35cfd64f13c6e456cc`. Apple clang 17 on arm64 built it with `c++ -O3 -std=c++17 n41_quotient_native_20261025.cpp -o n41_quotient_native_20261025`.

The checked field is `GF(2^41)` with modulus `z^41+z^3+1`; the curve is `y^2+xy=x^3+1`. For the third-product subspace `V`, the rank mode tests whether `c0` lies in the span of `c1*b+c2*b^2` over the seven pinned basis vectors `b`. The quotient mode normalizes by nonzero `c2`, constructs the linearized image vanisher of `p^2+(c1/c2)p` from the pinned subspace vanisher, and tests the normalized constant. A gate hit is checked against all 40 actual source products before it is recorded. The prior Lean module `RightQuotient_20261024.lean` covers the finite-subspace image-vanisher membership identity; the complete curve-to-coefficient construction is checked here by the frozen exact traversal and source-product replay.

Run from this directory:

```sh
python3 n41_quotient_native_prepare_20261025.py
c++ -O3 -std=c++17 n41_quotient_native_20261025.cpp -o n41_quotient_native_20261025
./n41_quotient_native_20261025 n41_quotient_native_input_20261025.tsv --rank
./n41_quotient_native_20261025 n41_quotient_native_input_20261025.tsv
```

## Matched run record

The preserved `n41_quotient_rank_abba_20261025.json` records the ABBA order, binary/input/source hashes, each complete JSON result, setup and query intervals, and raw platform RSS. Query traversal includes every root, including rejected roots and source-product checks after hits. Input preparation and parsing sit in setup. The two rank runs measured 1.99146 and 1.67203 seconds; the two quotient runs measured 6.03846 and 5.79245 seconds. Across these four observations, the quotient-to-rank query-time ratio spans 2.91–3.61. Frequency and host noise were not isolated, so the range is descriptive. The previously recorded direct group-index traversal for the same N41 witness took 1.323–1.333 seconds; this kernel comparison alone does not replace that traversal.

## Next gate

Use the direct-rank kernel as the baseline when evaluating exact multi-family constraints. A useful constraint must reject blocks before per-root checks while preserving the frozen witness. For transfer to a larger field, pin the coefficient stream and compare both kernels with the same root census before investing in a quotient-only path.
