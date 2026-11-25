# Prospective level-432 collision rule passes at p=1231

The frozen prediction was that a generic source triple `(C,E,B)` has two cyclic 16/27 source-chain keys exactly when `x_B³=1`, and one otherwise. A source-free sieve selected p=1231 without reading its source census. The complete inverse produced **1,368** rational triples: **72** with `x_B³=1`, each with two recovered chains, and **1,296** other triples, each with one. An independent all-j source census and image audit matched all **1,440** resulting chain keys, with zero missing, extra, or incorrect candidate sets.

| Frozen stage | Prime | Valid special triples | Status |
| --- | ---: | ---: | --- |
| Initial control full inverse screen | 1039 | 0 among 1,440 valid triples | Criterion untested |
| Adaptive source-free sieve | 1051 | 0 | Preserved zero cell |
| Adaptive source-free sieve | 1171 | 0 | Preserved zero cell |
| Selected holdout | **1231** | **72** | Prediction passed |

The prime rule was fixed before the sieve: scan ascending primes above 1039 with `p≡7 (mod 12)` and `−15` a nonzero square, stopping at the first with a valid source-free triple satisfying `x_B³=1`, below the cap 5000. The selected p1231 special B points are `(1,274)`, `(1,957)`, `(126,274)`, `(126,957)`, `(1104,274)`, and `(1104,957)`. They satisfy `y_B²=−15` and each has order 1213 in `B(F₁₂₃₁)`. Their double fibers account for 144 source chains; the other 1,296 triples account for 1,296 chains.

## Exact construction and audit

[`protocol.json`](protocol.json) froze p1039 and the initial prediction before its screen. [`sieve_protocol.json`](sieve_protocol.json) froze the adaptive selection rule and zero-cell policy before the sieve. [`holdout_protocol.json`](holdout_protocol.json) bound p1231 and the same prediction before its complete inverse screen; the source census was generated only after [`holdout_result.json`](holdout_result.json) was written. Every construction input is SHA-256 pinned. The inverse producer read no source census or source image.

The p1231 [source-free screen](screen_holdout.py) exhausts rational points on `C:y²+y=x³−7` and `E:y²=x³+432` against the exact degree-12 resolvent. All 1,368 pairs pass the rational branch filter. The checked-Sage [inverse producer](recover_holdout_sage.py) computes the gcd of the exact B-coordinate polynomial and `T³−x_E T²−64`, obtaining one rational B point at every pair. It derives source and intermediate j-invariants from C, enumerates cyclic 16/27 paths on the canonical generic source model, and matches 1,440 of 1,440 forward B evaluations. All encountered source j-invariants are generic.

The separately frozen [all-j census](source_census_sage.py) has 70 contributing source models and 1,440 cyclic path pairs. Its Hecke trace gives 1,464 rational `X₀(432)` points; an independent cusp count gives 24. The [source image](source_image_sage.py) evaluates all 1,440 path pairs. The pure-Python [holdout audit](audit_holdout.py) independently re-enumerates the 1,368 rational resolvent pairs, checks 1,368 polynomial Bézout and divisibility certificates, lifts every B point, and compares every exact source-chain candidate set to the all-j census and image. The receipt is [`holdout_audit.json`](holdout_audit.json). A separate [sieve audit](audit_sieve.py) reconstructs the special B test from the B polynomial and branch formula; its [receipt](sieve_audit.json) reproduces every zero and positive cell.

The source image and inverse producer share the previously verified modular forward evaluator, while their source enumerations and their use of C/E/B inputs are separate. The claim here is the exact finite-field collision rule at the selected prime; a characteristic-zero description of the collision divisor remains the next proof step. This is an IC stage diagnostic with `candidate_id: null`.

## Proof map

| Result | Lean declaration and verification |
| --- | --- |
| Every one of the 30 observed `x_B` classes has double fibers exactly at a cube root of one | `P1231ObservedGroups.double_iff_special`, kernel-checked from the compressed exact ledger in [`formal/ObservedGroups.lean`](formal/ObservedGroups.lean). The Python audit independently binds that ledger to all 1,368 rows and source keys. |
| 1,296 single plus 72 double triples give 1,440 source chains | `P1231ObservedGroups.single_double_totals` and `P1231ChainCoverage.fiber_total`, checked. |
| Duplicate-free generated and census chain keys with containment and equal count 1,440 are permutations | `P1231ChainCoverage.generated_keys_perm_sources`, checked from explicit hypotheses; the concrete containment is audited in Python. |
| Modular-curve maps and the generic collision divisor | Written finite-field construction above; a Lean definition of these modular maps and their integral models remains open. |

The [formal dependency record](formal/DEPENDENCIES.json) pins Lean 4.35.0-rc4 and records all `#print axioms` output. The observed ledger theorems have no axioms; the general list theorem uses only standard `propext`, `Classical.choice`, and `Quot.sound`. `lean4checker --fresh` is unavailable on this host.

Replay from the repository root:

```sh
python3 experiments/hecke-432-prime1039-collision-prediction-20261026/screen.py
python3 experiments/hecke-432-prime1039-collision-prediction-20261026/sieve.py
python3 experiments/hecke-432-prime1039-collision-prediction-20261026/screen_holdout.py
./sage --runtime-info > experiments/hecke-432-prime1039-collision-prediction-20261026/sage-runtime-info.txt
./sage -python experiments/hecke-432-prime1039-collision-prediction-20261026/recover_holdout_sage.py
./sage -python experiments/hecke-432-prime1039-collision-prediction-20261026/source_census_sage.py
./sage -python experiments/hecke-432-prime1039-collision-prediction-20261026/source_image_sage.py
python3 experiments/hecke-432-prime1039-collision-prediction-20261026/generate_formal.py
python3 experiments/hecke-432-prime1039-collision-prediction-20261026/audit_sieve.py
python3 experiments/hecke-432-prime1039-collision-prediction-20261026/audit_holdout.py
cd experiments/hecke-432-prime1039-collision-prediction-20261026/formal
lean ObservedGroups.lean
lean ChainCoverage.lean
cd .. && shasum -a 256 -c SEAL.sha256
```

The next experiment is to derive a characteristic-zero equation for the off-diagonal collision locus of the pair map `(C,B)` and test whether its B projection is the divisor `x_B³=1`, including special source j-values and ramified fibers as separate cases.
