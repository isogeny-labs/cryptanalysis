# X₀(11) trace fibers inside the full modular-curve point set

The reduced genus-one model of `X₀(11)` has **305, 900, and 1,020 points** over `F₃₁₇`, `F₉₄₁`, and `F₁₀₀₉`. Its regular finite points split into **20, 29, and 29 absolute-trace fibers** under the pinned source-curve `j` function. At the two archived D=-79 classes, the full regular fibers contain exactly **39** points at `(p,|t|)=(317,2)` and **40** at `(941,50)`. Their coordinate sets match the previously audited class-point lists, point for point.

This separates two sets that the original Hecke lead treated together: the image of the degree-one modular parametrization `X₀(11) → 11a1`, which covers the reduced elliptic curve's point set, and one trace-selected source fiber on which the archived Hecke relation collector operates. The census measures the latter's size and multiplicity at three primes. It does not infer a universal class-size bound from three cases.

## Frozen census

[The protocol](protocol.json) fixed `p ∈ {317,941,1009}` before the run, the 11a1 model `y²+y=x³−x²−10x−20`, the SHA-256 of the pinned `j=A(x,y)/(x−16)^11` coefficient table, the trace computation, and exceptional-point handling. The `j` table in [jfun.json](jfun.json) was extracted unchanged from the earlier degree-13 function artifact with SHA-256 `131d0dc58a1a92a5c8f7aa2f79870dbd3b906accd17e019ee0e72d054ebc86ac`. The extracted table's own SHA-256 is recorded in the protocol.

For every finite point of 11a1 over each field, [run.py](run.py) evaluates the pinned `j` function. For regular `j ≠ 0,1728`, it constructs `k=j/(1728−j)` and counts points on `y²=x³+3kx+2k` by the quadratic character. The absolute trace `|p+1−#E_j(F_p)|` is invariant under the two quadratic twists for these regular `j` values. It records infinity, both `x=16` denominator points, and any `j=0` or `1728` points separately. The full [point ledger](points.jsonl) and [result](result.json) retain every status and fiber count.

| `p` | `#X₀(11)(F_p)` | Regular points | `|t|` fibers | Largest fiber (`|t|`, points) | Archived D=-79 fiber |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 317 | 305 | 296 | 20 | `(12, 40)` | `(2, 39)` |
| 941 | 900 | 895 | 29 | `(18, 112)` | `(50, 40)` |
| 1009 | 1020 | 1017 | 29 | `(20, 84)` | — |

The nine exceptional finite/infinite points at `p=317`, five at `p=941`, and three at `p=1009` are retained in the result. The `|t|` partition deliberately combines quadratic-twist signs. It is a trace-magnitude partition of regular moduli points; individual Hecke relation components can be smaller. The finite panel alone gives no asymptotic fiber bound; the largest recorded fiber at `p=941` has 112 points, versus `√941≈30.7`.

## Verification and comparison

The independent [checked-Sage audit](audit_sage.py) rebuilt all three finite elliptic curves, enumerated their points, evaluated the same pinned rational `j` expression through Sage field arithmetic, checked each canonical curve's `j`-invariant and cardinality, and matched all **2,222 finite-point ledger rows** and three trace histograms. It passed with the repository Sage launcher and [runtime receipt](runtime-info.json); [audit-result.json](audit-result.json) pins the verified result hash.

The archive comparison was added **after** the complete new census. [archived-class-points.json](archived-class-points.json) retains the two prior point sets and their source-result hashes. [compare_archived.py](compare_archived.py) verifies exact set equality with the new `(317,2)` and `(941,50)` fibers, with [PASS receipt](archived-comparison-result.json). This is a retrospective identity check, separate from the preselected three-prime census.

The earlier [global Fricke result in PR #1195](https://github.com/isogeny-labs/cryptanalysis/pull/1195) records the degree-one modular parametrization and its model identification. That result's modular-curve identification is a written mathematical argument with a partial Lean bridge; this experiment adds exact finite-point and trace-fiber evidence. The next discriminating experiment is to measure the cost of moving from an arbitrary target's inverse image into the prepared trace fiber, including inverse-parametrization and cross-fiber connection work, against same-point rho.

From a full repository checkout, reproduce with:

```sh
python3 experiments/hecke-x011-trace-fiber-census-20261119/run.py
/Volumes/SSD990/cryptanalysis/sage --runtime-info > experiments/hecke-x011-trace-fiber-census-20261119/runtime-info.json
/Volumes/SSD990/cryptanalysis/sage -python experiments/hecke-x011-trace-fiber-census-20261119/audit_sage.py
python3 experiments/hecke-x011-trace-fiber-census-20261119/compare_archived.py
```

The archived comparison needs only the checked-in extracted point lists. No benchmark-tier wall-time claim is made from the local producer interval.
