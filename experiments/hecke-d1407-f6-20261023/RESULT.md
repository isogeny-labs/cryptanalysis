# A regular branch of the X₀(11) (j)-map restores the D = −1407 rank forecast

The prospective D = −1407, conductor-6 experiment now matches all 13 frozen class-quotient and signed-floor forecasts. Its checked-Sage relation matrix has **384 rational points, 288 verified Hecke rows, rank 240, and nonfloor projected rank 206**. The signed floor consists of 12 norm-2 cycles and 24 degree-3 pair differences. Each pair touches six distinct cycles; two balanced incidence components yield floor-direction rank 34.

The first producer run was a useful falsification of its own implementation: it returned 383 points, 286 rows, and rank 239. The (j)-evaluator rejected every point with (x=16), although only `(16 : −61 : 1)` is the pole of the chosen (j)-function. At the other point, `(16 : 60 : 1)`, the numerator cancels the denominator to order 11 and the regular value is exactly **(j=-121)**. In the chosen field (mathbf F_{12763}), this is 12642. The repaired evaluator admits that point and restores precisely two rows; all 286 old rows remain unchanged after reindexing by point identity.

## Frozen instance and measured rows

`MODEL_BEFORE_HOLDOUT.json` and `protocol_D1407.json` were saved before either producer run. They fixed fundamental discriminant `−1407`, conductor `6`, field prime `12763`, trace `20` (`20²−4·12763=−1407·6²`), Hecke degrees 2 and 3, and the predictions below. The model was fitted to 11 previously audited discriminants and made this case a prospective holdout.

| Quantity | Frozen prediction | First evaluator | Regularized evaluator |
| --- | ---: | ---: | ---: |
| Rational class points | 384 | 383 | 384 |
| Degree-2 / degree-3 verified rows | 192 / 96 | 191 / 95 | 192 / 96 |
| Full rank over Q | 240 | 239 | 240 |
| Nonfloor projected rank over Q | 206 | 206 | 206 |
| Signed norm-2 cycles | 12 | 11 complete, one cut | 12 |
| Exact degree-3 floor pairs | 24 | 23, one singleton | 24 |
| Balanced incidence components | 2 | one intact, one cut | 2 |
| Floor-direction rank | 34 | 33 | 34 |

The first result is retained under `data/`, `launch.json`, `audit_exception.json`, `floor_exception.json`, and `partial_graph.json`. An independent enumeration of the four CM ring-class polynomials found every point reported by that evaluator, but its conductor-6 fiber above (j=12642) contained only one point because `Reduced.j` returned `None` on the regular (x=16) branch. Two otherwise complete saved Hecke neighbor sets led to the omitted point. The exact partial graph had components of five cycles/11 pairs (rank 16) and six cycles/12 pairs (rank 17), explaining its 33 floor directions.

The repaired version lives under `regularized/`, with its own source hashes, two-sheet gate, frozen rerun protocol, producer receipt, independent Sage audit, floor audit, graph audit, and pure-Python integer/rational validation. The repaired two-sheet gate counts 48, 48, 144, and 144 rational points for conductors 1, 2, 3, and 6. The independent Sage audit reconstructs each point, conductor, modular-polynomial root count, saved elliptic-curve row identity, and ranks over Q, 23, 1000000007, and 2147483647. `regularized/validation_D1407.json` independently replays the signed cycle and pair vectors and all projected ranks. `forecast_comparison.json` compares the repaired evidence against 13 fields of the pre-run model with zero mismatches.

## Exact branch proof and formalization

Write the numerator of the explicit (j)-function as (A_0(x)+A_1(x)y), with denominator ((x-16)^{11}), on the curve (y^2+y=x^3-x^2-10x-20). The exact identity is

\[
 A_0(x)^2-A_0(x)A_1(x)-A_1(x)^2(x^3-x^2-10x-20)
 =-(x-16)^{11}F(x)^3,
\]

where (F(x)=x^4-52820x^3+1333262x^2+4971236x+9789217). The numerator on the conjugate branch (y=-61) at (x=16) is (81402749386839761113321\ne0). Therefore, on the regular branch (y=60), cancellation gives the extension

\[
 j_{\mathrm{reg}}(x,y)=\frac{-F(x)^3}{A_0(x)+A_1(x)(-1-y)},
 \qquad j_{\mathrm{reg}}(16,60)=-121.
\]

`exact_regular_j.json` computes the same value over Q, and `local_j_limit.json` verifies all 11 lower coefficients vanish modulo 12763 while the cusp branch has a nonzero constant numerator. The generated [Lean theorem module](formal/RegularBranch.lean) proves the displayed polynomial norm identity, both (x=16) points' curve equations, the nonzero conjugate denominator, the value (-121), and equality with the original quotient away from (x=16). The module is built with pinned Lean `v4.35.0-rc4` and Mathlib revision `021c46bdd042f67b538b9f9871d556a93713a9a9`; `formal/regular-branch-check.txt` records `#print axioms` with only `propext`, `Classical.choice`, and `Quot.sound`. `lean4checker --fresh` was unavailable on this host. The exact source coefficients and generator hash are retained in `formal/regular-branch-generation.json`.

The broader class-action formula still has a distinct proof obligation: identify the actual rational (X_0(11)) sheets, norm-2 steps, and ramified degree-3 pairing uniformly with their ideal-class cosets. The repaired D = −1407 result is the twelfth audited case consistent with the quotient/sign rank model. Future runs should execute `fiber_gate.py` with the regularized evaluator before making a two-sheet rank forecast, then preregister a discriminant with a new quotient/sign configuration. These are stage-level rank measurements with `candidate_id: null` and `timing_claim: null`.

## Reproduction

Use `/Volumes/SSD990/cryptanalysis/sage` for every Sage command. The key frozen and replay records are `protocol_D1407.json`, `regularized/protocol_regularized.json`, `regularized/launch.json`, `regularized/audit_D1407.json`, `regularized/floor_D1407.json`, `regularized/graph_D1407.json`, `regularized/validation_D1407.json`, `repair_delta.json`, and `forecast_comparison.json`. The two producer outputs are separately retained and bound by SHA-256 receipts. `SEAL.json` hashes the full reviewable bundle.
