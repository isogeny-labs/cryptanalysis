# The 27-by-16 source-fiber product predicts the j=1728 fibers at p=1439

A frozen product rule predicted all seven valid `j=1728` source-fiber multiplicities at the fresh prime **p=1439**. The two audited priors, p1319 and p1367, each had exactly **one cyclic 16-path index per matched rational 27-path/B cell**. Multiplying this measured unit factor by the p1439 rational 27-path j-sequence count predicted **four double fibers and three empty fibers** before the p1439 cyclic 16-path inverse or all-j census ran. The complete inverse and independent source image matched every prediction. The p1439 image also measured a unit 16-path factor in all eight observed special-j cells.

| C point | Source/intermediate/target j-sequence in `F_1439` | Valid triples | Rational 27 paths | Prior 16-path B factor | Observed chains per triple |
| --- | --- | ---: | ---: | ---: | ---: |
| `(565,949)` | `(289,9,880,531)` | 3 | 0 | 1 | 0 |
| `(789,794)` | `(289,707,249,1416)` | 4 | 2 | 1 | 2 |

The empty C sheet includes a valid sign-branch triple with `B=(653,0)`; its restricted Jacobian is critical, but its rational 27-path count is zero. On the other sheet, two rational 27-paths share the same j-sequence and each matched B point has one cyclic 16-path index. This explains the four multiplicity-two fibers in the finite-field audit.

## Frozen stages and independent checks

[`factor_protocol.json`](factor_protocol.json) bound the p1319 and p1367 independent all-j images before [`factor.py`](factor.py) measured eight unit-factor cells per prime. [`sieve_protocol.json`](sieve_protocol.json) then froze the source-free third-prime rule: scan ascending primes above 1367 with `p≡23 (mod 24)` and select the first with at least four valid `j=1728` triples on two rational C sheets. The [sieve](sieve.py) selected p1439, its first eligible prime; the [independent arithmetic replay](audit_sieve.py) matched all seven selected rows.

[`protocol.json`](protocol.json) froze the complete p1439 source-free [screen](screen.py), which found **1,376** valid rational C/E/B triples. [`prediction_protocol.json`](prediction_protocol.json) fixed the 27-path-count times prior unit-factor rule before the checked-Sage [predictor](predict_product_sage.py) ran. Its [result](prediction_result.json) recorded four 2s and three 0s without reading p1439 cyclic 16 paths, B forward image, or source-chain multiplicities. [`inverse_protocol.json`](inverse_protocol.json) bound those predictions before the complete checked-Sage [inverse](recover_sage.py), which matched **1,384** forward chains with multiplicity histogram **3 empty, 1,362 single, 11 double** and zero primary mismatches.

[`source_protocol.json`](source_protocol.json) was frozen after the inverse, binding an independent all-j [census](source_census_sage.py) and [forward image](source_image_sage.py). The census enumerated 173 contributing models and 1,384 source chains. Its Hecke count is **1,392** rational `X₀(432)` points, including **8** rational cusps. The [independent audit](audit.py) re-enumerated every rational resolvent pair, checked 1,376 polynomial Bézout certificates and B lifts, recomputed restricted gradients by truncated dual numbers, matched every source candidate set, replayed the seven frozen product predictions against the all-j census, and measured the third-prime 16-path factor. Its [receipt](audit.json) is `PASS_P1439_INDEPENDENT_PRODUCT_AUDIT`. The checked Sage [runtime receipt](sage-runtime-info.txt) and [audit helper hashes](audit_dependencies.json) are retained.

## Proof map and next step

The field-algebra sign-branch identity is Lean-checked in [`SignBranch.lean`](../hecke-432-collision-singular-locus-20261026/formal/SignBranch.lean). The local Lean [`ProductLedger.lean`](formal/ProductLedger.lean) checks the seven exact triples, the frozen numerical `27-path count × 16-path factor` equation, their observed multiplicities, and the four double/three empty totals. [`generate_formal.py`](generate_formal.py) derives this ledger from the independent audit receipt. The actual build and `#print axioms` results are recorded in [`formal/build-output.txt`](formal/build-output.txt), with pinned toolchain and Mathlib revisions in [`formal/DEPENDENCIES.json`](formal/DEPENDENCIES.json). The modular-curve source-chain maps and special-j stabilizer action remain to be defined and proved in Lean; the finite-field map, counts, and matching are checked by the sealed producers and audits.

The next experiment should test a different congruence class, beginning with `p≡7 (mod 24)`, where cubic-twist and rational 27-path behavior can differ. Freeze the source-free prime choice and product rule before the full inverse, preserving special `j=0` cases separately. A structural proof should identify the stabilizer orbit that makes the 16-path B factor one in the measured `p≡23 (mod 24)` cells. This is an IC stage diagnostic with `candidate_id: null`.

Replay from the repository root:

```sh
python3 experiments/hecke-432-j1728-product-holdout-20261026/factor.py
python3 experiments/hecke-432-j1728-product-holdout-20261026/sieve.py
python3 experiments/hecke-432-j1728-product-holdout-20261026/screen.py
./sage --runtime-info > experiments/hecke-432-j1728-product-holdout-20261026/sage-runtime-info.txt
./sage -python experiments/hecke-432-j1728-product-holdout-20261026/predict_product_sage.py
./sage -python experiments/hecke-432-j1728-product-holdout-20261026/recover_sage.py
./sage -python experiments/hecke-432-j1728-product-holdout-20261026/source_census_sage.py
./sage -python experiments/hecke-432-j1728-product-holdout-20261026/source_image_sage.py
python3 experiments/hecke-432-j1728-product-holdout-20261026/audit_sieve.py
python3 experiments/hecke-432-j1728-product-holdout-20261026/audit.py
python3 experiments/hecke-432-j1728-product-holdout-20261026/generate_formal.py
cd experiments/hecke-432-formal-ci-20261025 && lake env lean ../hecke-432-j1728-product-holdout-20261026/formal/ProductLedger.lean
cd ../hecke-432-j1728-product-holdout-20261026 && shasum -a 256 -c SEAL.sha256
```
