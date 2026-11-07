# A prospective sign-branch holdout isolates the j=1728 exception

At the fresh prime **p=1319**, four rational `C,E,B` triples satisfy `y_B=0`, `D_C P_B=0`, and `∂_T P_B≠0`. The frozen restricted-Jacobian rule predicted two cyclic 16/27 source-chain keys at each; the direct inverse and independent all-j image found **two at all four**. Across the complete valid set of **1,296** triples, the rule matches every **1,280 generic-source** triple. Its preregistered all-triples extension fails at eight `j=1728` triples: four have two keys where one was predicted, and four have none where one was predicted.

| Source class | Restricted-Jacobian prediction | Observed source chains per triple | Triples | B sign branch |
| --- | --- | ---: | ---: | --- |
| Generic j | singleton | 1 | 1,272 | no |
| Generic j | double | 2 | 4 | no |
| Generic j | double | 2 | 4 | yes, `y_B=0` and `∂_T P_B≠0` |
| `j=0` | singleton | 1 | 8 | no |
| `j=1728` | singleton | 0 | 4 | no |
| `j=1728` | singleton | 2 | 4 | no |

The four selected sign-branch triples share `B=(1176,0)` and `E=(429,0)`; their C points are `(350,194)`, `(973,297)`, `(1061,226)`, and `(1077,1215)`. The respective nonzero `∂_T P_B` values are 3, 175, 541, and 227. The branch is critical because its restricted B derivative is `2y_B∂_T P_B=0`.

## Frozen selection and complete inverse

[`sieve_protocol.json`](sieve_protocol.json) fixed the selection rule before the search: scan ascending primes above 1279 and below 5000, selecting the first with a valid rational `y_B=0`, `D_C P_B=0`, `∂_T P_B≠0` triple. The [sieve](sieve.py) recorded zero critical cells at 1283, 1289, 1301, and 1307, then selected 1319 with four. An [independent sieve audit](audit_sieve.py) re-enumerated the eligible primes, rational C points, exact resolvent and branch equations, and dual-number gradients; its [receipt](sieve_audit.json) matches all five cells.

[`protocol.json`](protocol.json) then froze the selected prime and the prediction for every valid rational triple before the [source-free screen](screen.py). The screen found 1,308 resolvent pairs: **1,296 valid**, eight `ZERO_DENOMINATOR`, and four `Y_INVERSE_UNDEFINED`. It predicted eight double fibers: the four selected sign-branch triples and four polynomial critical triples. [`inverse_protocol.json`](inverse_protocol.json) bound those rows before the checked-Sage [direct inverse](recover_sage.py). The inverse yielded the honest status `FAIL_P1319_PROSPECTIVE_JACOBIAN_PREDICTION`, with multiplicity histogram **4 empty, 1,280 single, 12 double** and 1,304 matched forward chains. All eight prediction mismatches are at `j=1728`.

[`source_protocol.json`](source_protocol.json) was frozen after the direct inverse, binding the independent all-j [source census](source_census_sage.py) and [forward image](source_image_sage.py). The census enumerated 163 contributing source models and **1,304** chain keys. Its Hecke count is **1,312** rational `X₀(432)` points, of which **8** are rational cusps. The independent [audit](audit.py) re-enumerates all resolvent pairs, checks 1,296 polynomial Bézout certificates and B lifts, recomputes gradients with truncated dual numbers, and compares every source candidate set, including the four empty sets. Its [receipt](audit.json) reports `PASS_P1319_INDEPENDENT_EXCEPTION_AUDIT`, zero missing or extraneous chain-bearing images, and zero incorrect candidate sets. The checked Sage [runtime receipt](sage-runtime-info.txt) and [audit dependency hashes](audit_dependencies.json) are included.

## Proof map and next step

The field-algebra identity for the restricted B derivative and the `y_B=0` sign branch is proved in the pinned Lean module [`SignBranch.lean`](../hecke-432-collision-singular-locus-20261026/formal/SignBranch.lean). The local Lean [`ObservedClasses.lean`](formal/ObservedClasses.lean) checks the compressed p1319 class ledger: the generic-class rule, the four selected sign-branch observations, eight `j=1728` exceptions, total 1,296 triples, and 1,304 chain keys. [`generate_formal.py`](generate_formal.py) derives that ledger from the independent audit receipt; the actual build and `#print axioms` results are in [`formal/build-output.txt`](formal/build-output.txt), with pinned toolchain and Mathlib revisions in [`formal/DEPENDENCIES.json`](formal/DEPENDENCIES.json). These Lean declarations verify the exact ledger arithmetic. The modular-curve normalization map, special-j stabilizer action, and source-fiber multiplicity bridge remain open formal definitions and proofs.

The p1319 data suggests a concrete correction: analyze the `j=1728` automorphism stabilizer on cyclic 16/27 chains and compare normalized source fibers to the coarse `C×B` Jacobian. A prospective special-j holdout should freeze the resulting stabilizer-weighted prediction before another all-j census. This is an IC stage diagnostic with `candidate_id: null`.

Replay from the repository root:

```sh
python3 experiments/hecke-432-sign-branch-holdout-20261026/sieve.py
python3 experiments/hecke-432-sign-branch-holdout-20261026/screen.py
./sage --runtime-info > experiments/hecke-432-sign-branch-holdout-20261026/sage-runtime-info.txt
./sage -python experiments/hecke-432-sign-branch-holdout-20261026/recover_sage.py
./sage -python experiments/hecke-432-sign-branch-holdout-20261026/source_census_sage.py
./sage -python experiments/hecke-432-sign-branch-holdout-20261026/source_image_sage.py
python3 experiments/hecke-432-sign-branch-holdout-20261026/audit_sieve.py
python3 experiments/hecke-432-sign-branch-holdout-20261026/audit.py
python3 experiments/hecke-432-sign-branch-holdout-20261026/generate_formal.py
cd experiments/hecke-432-formal-ci-20261025 && lake env lean ../hecke-432-sign-branch-holdout-20261026/formal/ObservedClasses.lean
cd ../hecke-432-sign-branch-holdout-20261026 && shasum -a 256 -c SEAL.sha256
```
