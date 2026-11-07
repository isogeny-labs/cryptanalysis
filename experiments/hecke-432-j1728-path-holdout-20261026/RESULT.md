# Rational 27-path signatures predict the j=1728 source fibers at p=1367

A frozen **p=1367** predictor used only rational cyclic 27-path j-sequences on the canonical `j=1728` source. It predicted **two source chains at four valid triples** on one rational C sheet and **zero at three triples** on another. The complete cyclic 16/27 inverse and independent all-j forward image matched all seven predictions. This gives a concrete, prospective correction for the special-j fibers that broke the all-triples restricted-Jacobian rule at p1319.

| C point | Computed source/intermediate/target j-sequence over `F_1367` | Valid triples | Frozen 27-path count | Observed chains per triple |
| --- | --- | ---: | ---: | ---: |
| `(286,538)` | `(361,303,70,72)` | 4 | 2 | 2 |
| `(920,172)` | `(361,273,1263,918)` | 3 | 0 | 0 |

The canonical `j=1728` source has two rational cyclic 27-paths, both with the first j-sequence. The second C sheet has no matching rational 27-path. One of its three valid triples has `B=(340,0)` and a critical restricted Jacobian, yet its source-chain fiber is empty. The other four doubles and three empty fibers agree with the preregistered path-signature counts.

## Frozen selection and audit

[`sieve_protocol.json`](sieve_protocol.json) selected the first prime above 1319 with `p≡23 (mod 24)` and at least four valid `j=1728` triples on two distinct rational C points. The [source-free sieve](sieve.py) selected p1367, the first eligible prime; an [independent arithmetic replay](audit_sieve.py) matched its seven valid rows. [`protocol.json`](protocol.json) then froze the complete source-free [screen](screen.py): **1,380** rational resolvent pairs, **1,376 valid** triples, and four `ZERO_DENOMINATOR` rows.

[`prediction_protocol.json`](prediction_protocol.json) fixed the path-count rule before the [27-path producer](predict_27_sage.py) ran. That producer enumerated only cyclic 27 paths on `E:y²=x³+x` over `F_1367` and compared their j-sequences with the exact coordinate maps evaluated at the seven selected C/E/B triples. It read no cyclic 16-path data, B forward image, full source census, or p1367 chain multiplicities. [`prediction_result.json`](prediction_result.json) froze the four 2s and three 0s before [`inverse_protocol.json`](inverse_protocol.json) bound the complete checked-Sage [inverse](recover_sage.py).

The inverse recovered **1,384** matched source chains across the 1,376 valid triples, with multiplicity histogram **3 empty, 1,362 single, 11 double** and zero failures of the seven primary predictions. The coarse restricted-Jacobian baseline disagreed on exactly those seven `j=1728` triples; its generic-source rows matched. The independent all-j [census](source_census_sage.py) enumerated 173 contributing source models and 1,384 chain keys. Its Hecke count is **1,392** rational `X₀(432)` points, including **8** rational cusps. The separate [forward image](source_image_sage.py) evaluates all 1,384 keys.

The [independent audit](audit.py) re-enumerates all resolvent pairs, verifies **1,376** polynomial Bézout certificates and B lifts, recomputes all restricted derivatives by truncated dual numbers, compares every candidate set with the complete forward image, and independently recovers the two rational 27-path signatures from the all-j census. Its [receipt](audit.json) reports `PASS_P1367_INDEPENDENT_27_PATH_AUDIT` with zero primary mismatches and exact candidate-set agreement. Both [audit helper dependencies](audit_dependencies.json) and the checked Sage [runtime receipt](sage-runtime-info.txt) are preserved.

## Proof map and next experiment

The field-algebra restricted-Jacobian identity is Lean-checked in [`SignBranch.lean`](../hecke-432-collision-singular-locus-20261026/formal/SignBranch.lean). The local Lean [`PathLedger.lean`](formal/PathLedger.lean) checks the seven exact predicted/observed triples, their four double and three empty counts, and their eight source chains. [`generate_formal.py`](generate_formal.py) derives that ledger from the independent audit receipt; the actual build and `#print axioms` are in [`formal/build-output.txt`](formal/build-output.txt), with pinned dependencies in [`formal/DEPENDENCIES.json`](formal/DEPENDENCIES.json). The modular-curve path map and stabilizer action are verified by the frozen finite-field producers and audit; their full Lean definitions and proof remain open.

The next test is a factorization of special-j fiber size into **rational 27-path multiplicity** and a **16-path B-fiber factor**. Compute the latter independently at p1319 and p1367, then freeze the product rule for a third prime, including the `y_B=0` case and both `j=0` and `j=1728`. This is an IC stage diagnostic with `candidate_id: null`.

Replay from the repository root:

```sh
python3 experiments/hecke-432-j1728-path-holdout-20261026/sieve.py
python3 experiments/hecke-432-j1728-path-holdout-20261026/screen.py
./sage --runtime-info > experiments/hecke-432-j1728-path-holdout-20261026/sage-runtime-info.txt
./sage -python experiments/hecke-432-j1728-path-holdout-20261026/predict_27_sage.py
./sage -python experiments/hecke-432-j1728-path-holdout-20261026/recover_sage.py
./sage -python experiments/hecke-432-j1728-path-holdout-20261026/source_census_sage.py
./sage -python experiments/hecke-432-j1728-path-holdout-20261026/source_image_sage.py
python3 experiments/hecke-432-j1728-path-holdout-20261026/audit_sieve.py
python3 experiments/hecke-432-j1728-path-holdout-20261026/audit.py
python3 experiments/hecke-432-j1728-path-holdout-20261026/generate_formal.py
cd experiments/hecke-432-formal-ci-20261025 && lake env lean ../hecke-432-j1728-path-holdout-20261026/formal/PathLedger.lean
cd ../hecke-432-j1728-path-holdout-20261026 && shasum -a 256 -c SEAL.sha256
```
