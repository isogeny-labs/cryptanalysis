# X₀(11) trace fibers inside the full modular-curve point set

The reduced genus-one model of `X₀(11)` has **305, 900, and 1,020 points** over `F₃₁₇`, `F₉₄₁`, and `F₁₀₀₉`. Its regular finite points split into **20, 29, and 29 absolute-trace fibers** under the pinned source-curve `j` function. The [versioned correction](AMENDMENT.md) evaluates the removable branch at `(16,60)`, where `j=-121` exactly. The corrected regular fibers contain **40** points at `(p,|t|)=(317,2)` and **40** at `(941,50)`. The previously audited `p=317` class-point list contains 39 of those 40 points; its rank result therefore applies to the saved 39-column submatrix.

This separates two sets that the original Hecke lead treated together: the image of the degree-one modular parametrization `X₀(11) → 11a1`, which covers the reduced elliptic curve's point set, and one trace-selected source fiber on which the archived Hecke relation collector operates. The census measures the latter's size and multiplicity at three primes. It does not infer a universal class-size bound from three cases.

## Frozen census

[The protocol](protocol.json) fixed `p ∈ {317,941,1009}` before the run, the 11a1 model `y²+y=x³−x²−10x−20`, the SHA-256 of the pinned `j=A(x,y)/(x−16)^11` coefficient table, the trace computation, and exceptional-point handling. The `j` table in [jfun.json](jfun.json) was extracted unchanged from the earlier degree-13 function artifact with SHA-256 `131d0dc58a1a92a5c8f7aa2f79870dbd3b906accd17e019ee0e72d054ebc86ac`. The extracted table's own SHA-256 is recorded in the protocol.

For every finite point of 11a1 over each field, the original [run.py](run.py) evaluated the pinned expression wherever its displayed denominator was nonzero. That v1 run recorded both `x=16` points as exceptions. The [v2 producer](run_v2.py) retains the original ledger and corrects the removable point `(16,60)` using its order-11 local expansion. It records the genuine pole `(16,-61)` separately. The corrected [point ledger](points_v2.jsonl.gz) and [result](result_v2.json) retain every status and fiber count, with raw and compressed SHA-256 digests.

| `p` | `#X₀(11)(F_p)` | Regular points | `|t|` fibers | Largest fiber (`|t|`, points) | Archived D=-79 fiber |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 317 | 305 | 297 | 20 | `(2, 40)` and `(12, 40)` | `(2, 40)`; archived list 39 |
| 941 | 900 | 896 | 29 | `(18, 112)` | `(50, 40)` |
| 1009 | 1020 | 1018 | 29 | `(20, 84)` | — |

The corrected exceptional finite/infinite counts are eight at `p=317`, four at `p=941`, and two at `p=1009`. The `|t|` partition deliberately combines quadratic-twist signs. It is a trace-magnitude partition of regular moduli points; individual Hecke relation components can be smaller. The finite panel alone gives no asymptotic fiber bound; the largest recorded fiber at `p=941` has 112 points, versus `√941≈30.7`.

## Verification and comparison

The original [checked-Sage audit](audit_sage.py) verified the v1 finite-point ledger under its stated denominator-exclusion policy. The [v2 checked-Sage audit](audit_v2_sage.py) independently divides the exact integer polynomial norm of the numerator by `(x−16)^11`, checks zero remainder and the quotient value giving `j(16,60)=-121`, verifies that only three ledger rows change, and recounts their canonical curves. It passed on all **2,222 finite-point rows** with the repository Sage launcher; [audit-v2.json](audit-v2.json) and [runtime-v2.json](runtime-v2.json) retain its receipts.

The archive comparison was added **after** the original census. [archived-class-points.json](archived-class-points.json) retains the two prior point sets and their source-result hashes. Its [v1 comparison](archived-comparison-result.json) passed under the v1 exclusion policy. Under v2, the p317 list is missing `(16,60)`; the p941 `(50)` list remains complete. The original receipt remains frozen, and the discrepancy is recorded in [AMENDMENT.md](AMENDMENT.md).

The earlier [global Fricke result in PR #1195](https://github.com/isogeny-labs/cryptanalysis/pull/1195) records the degree-one modular parametrization and its model identification. That result's modular-curve identification is a written mathematical argument with a partial Lean bridge; this experiment adds exact finite-point and trace-fiber evidence. The next discriminating experiment is to measure the cost of moving from an arbitrary target's inverse image into the prepared trace fiber, including inverse-parametrization and cross-fiber connection work, against same-point rho.

From a full repository checkout, reproduce with:

```sh
python3 experiments/hecke-x011-trace-fiber-census-20261119/run.py
/Volumes/SSD990/cryptanalysis/sage --runtime-info > experiments/hecke-x011-trace-fiber-census-20261119/runtime-info.json
/Volumes/SSD990/cryptanalysis/sage -python experiments/hecke-x011-trace-fiber-census-20261119/audit_sage.py
python3 experiments/hecke-x011-trace-fiber-census-20261119/compare_archived.py
python3 experiments/hecke-x011-trace-fiber-census-20261119/run_v2.py
/Volumes/SSD990/cryptanalysis/sage --runtime-info > experiments/hecke-x011-trace-fiber-census-20261119/runtime-v2.json
/Volumes/SSD990/cryptanalysis/sage -python experiments/hecke-x011-trace-fiber-census-20261119/audit_v2_sage.py
```

The archived comparison needs only the checked-in extracted point lists. No benchmark-tier wall-time claim is made from the local producer interval.
