# The regular (x=16) branch affects one archived Hecke class instance

The exact (X_0(11)) point `(16 : 60 : 1)` has (j=-121), as proved in the adjacent [D = −1407 regular-branch experiment](../hecke-d1407-f6-20261023/RESULT.md). A frozen census of **63 saved class-walk outputs at 27 distinct primes** found that this point lies in the recorded trace and conductor class only for D = −1407, conductor 6. The original 383-point output omits it; the repaired 384-point output includes it. A second copy of the original output in the external research bundle has the same omission. The other 60 archived outputs have a different Frobenius trace for (j=-121), so this particular branch omission cannot change their saved class matrices.

## Method and evidence boundary

`protocol.json` freezes 25 workspace outputs and their producer-source hashes. `external_protocol.json` separately freezes 38 external sealed outputs by exact absolute path and SHA-256. The cases include repeated D = −1407, conductor-20 receipts from performance experiments; 63 is an artifact count, not a count of independent discriminants. Both protocols were written before their checked-Sage trace classifications. The local `/Volumes/SSD990/cryptanalysis/sage --runtime-info` receipt precedes the runs.

For every distinct prime (p), the Sage census constructs the elliptic curve with (j=-121\pmod p), computes the absolute Frobenius trace and endomorphism-order conductor, and compares them with each saved `(D_K,f,p,u)` and point list. A case is flagged only when the absolute trace equals `u`, the conductor divides `f`, the saved class is nonempty, and `(16 : 60 : 1)` is absent. `RESULT.json` and `external_result.json` retain every case and prime fact, including the failed and repaired D = −1407 controls.

| Scope | Saved outputs | Distinct primes | Eligible omitted point |
| --- | ---: | ---: | --- |
| Workspace archive | 25 | 19 | Original D = −1407, f = 6 |
| External research bundles | 38 | 9 | Copy of original D = −1407, f = 6 |
| Combined | 63 | 27 | One mathematical instance, saved twice |

The independent validator uses direct Legendre-symbol point counts for the 19 workspace primes and the seven external primes below 100,000. For the two larger external primes it constructs an explicit short-Weierstrass model with the same (j) and uses PARI `ellcard`. All 27 absolute traces match the Sage census. In particular, the D = −1407, conductor-20 receipts use `p=19439149,u=8786` or `p=1052299669,u=64874`; their independent (j=-121) traces are `5893` and `−42986`, respectively. These two large-prime classes therefore do not contain the regular branch. The frozen validation protocols and complete receipts are `validation_protocol.json`, `validation.json`, `external_validation_protocol.json`, and `external_validation.json`.

This census establishes the scope of the **specific** broad-`x=16` guard defect across the enumerated saved outputs. The D = −1407 experiment separately reconstructs all points and rows after repair, proves the rational (j=-121) extension in Lean, and compares the two producer matrices point by point. Future class-walk producers should use the regularized evaluator and its two-sheet fiber gate before interpreting a quotient-rank forecast. The remaining uniform class-action proof and full IC accounting are separate research steps. The census records `candidate_id: null` and `timing_claim: null`.
