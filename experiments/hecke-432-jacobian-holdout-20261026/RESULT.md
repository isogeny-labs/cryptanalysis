# Prospective restricted-Jacobian collision prediction passes at p=1279

The frozen restricted-Jacobian rule predicted **72 double fibers** among **936** valid rational `C,E,B` triples over `F_1279`. A direct checked-Sage inverse recovered **72 doubles and 864 singletons**, with zero prediction mismatches. The independent all-j source census has **1,008 cyclic 16/27 chains**; its complete forward image agrees with every recovered candidate set. The finite-field result extends the earlier exploratory five-prime classification to a fresh prospective prime.

| Stage | Exact result |
| --- | --- |
| Prime selection | First prime `p>1231` with `p≡7 (mod 12)` and `−15` a nonzero square: `p=1279` |
| Source-free resolvent screen | 936 rational pairs; all yield one valid `C,E,B` triple |
| Frozen rule | Double iff `D_C P_B=0` and `2y_B ∂_T P_B=0` |
| Source-free prediction | 72 doubles, 864 singletons |
| Direct inverse | 1,008 matched forward chains; 72 doubles, 864 singletons; zero unmatched outputs |
| Independent source census | 52 source models, 1,008 chain keys; Hecke count 1,032 with 24 cusps |
| Independent audit | 936 polynomial Bézout certificates, 936 dual-number gradient checks, exact candidate-set equality, zero prediction mismatches |

The six B points above the double locus are `(1,143)`, `(1,1136)`, `(504,143)`, `(504,1136)`, `(774,143)`, and `(774,1136)`. All 72 double triples satisfy `∂_T P_B=D_C P_B=0` with `y_B≠0`; the sign-branch case at `y_B=0` remains represented by the earlier p887 measurements. No p1279 source-chain multiplicity was consulted in the source-free screen or its frozen prediction.

## Construction and verification

[`protocol.json`](protocol.json) fixes p1279, the input hashes, and the Jacobian prediction before the [source-free screen](screen.py). [`inverse_protocol.json`](inverse_protocol.json) binds its 936 predicted rows before the [direct inverse](recover_sage.py). The inverse intersects the exact B-coordinate polynomial with the E-to-B cubic, lifts the rational B point, and enumerates cyclic source chains against the forward map. [`source_protocol.json`](source_protocol.json) was frozen only after that inverse finished and binds the independently generated all-j [census](source_census_sage.py) and [image](source_image_sage.py).

The independent [audit](audit.py) re-enumerates every rational resolvent pair, recomputes `D_C P_B` and `∂_T P_B` by truncated dual numbers, checks 936 polynomial Bézout identities and B lifts, compares all 1,008 source-chain keys with the independent image, and verifies the Hecke-minus-cusps count. Its [receipt](audit.json) reports `PASS_P1279_INDEPENDENT_JACOBIAN_AUDIT`. The audit's imported arithmetic helpers are hash-pinned in [`audit_dependencies.json`](audit_dependencies.json). All local Sage runs used the repository's checked launcher; its runtime receipt is [`sage-runtime-info.txt`](sage-runtime-info.txt).

The algebraic step `D_B P_B=2y_B∂_T P_B` and its sign-branch disjunction are proved in the pinned Lean module [`SignBranch.lean`](../hecke-432-collision-singular-locus-20261026/formal/SignBranch.lean), with build and axiom receipts there. The p1279 row classification is an empirical finite-field claim backed by the complete audited ledger; a Lean definition of the modular maps and a kernel proof over that ledger remain open. This is an IC stage diagnostic with `candidate_id: null`.

The next proof step is to identify the characteristic-zero critical divisor of the `C×B` map and establish its relation to source-chain multiplicity, including the `y_B=0` branch and special source j-values. A further prime selected to exercise the sign branch would give a second prospective exception test.

Replay from the repository root:

```sh
python3 experiments/hecke-432-jacobian-holdout-20261026/screen.py
./sage --runtime-info > experiments/hecke-432-jacobian-holdout-20261026/sage-runtime-info.txt
./sage -python experiments/hecke-432-jacobian-holdout-20261026/recover_sage.py
./sage -python experiments/hecke-432-jacobian-holdout-20261026/source_census_sage.py
./sage -python experiments/hecke-432-jacobian-holdout-20261026/source_image_sage.py
python3 experiments/hecke-432-jacobian-holdout-20261026/audit.py
cd experiments/hecke-432-jacobian-holdout-20261026 && shasum -a 256 -c SEAL.sha256
```
