# Single-sided quartic splitting transfer at five new primes

The exact `s -> -s` conjugacy let one quartic supply **all 68** local splitting predictions for the other quartic at rational primes 41, 43, 47, 53, and 59. The prediction file was SHA-256 sealed before any right-quartic observation. All 68 predictions matched: 62 were checked by squarefree right-quartic residue factorization. At the six repeated reductions at primes 43 and 59, a normalized Taylor quadratic resolved the double-root cluster directly from the right quartic; right-side Kummer unit characters independently agreed. This gives a complete method-labelled local check across the five-prime set without factoring the right quartic in the prediction stage.

| Rational prime | Base places | `[1,1,1,1]` | `[2,2]` | Observation method |
| ---: | ---: | ---: | ---: | --- |
| 41 | 6 | 0 | 6 | 6 squarefree reductions |
| 43 | 18 | 18 | 0 | 15 squarefree reductions, 3 Taylor checks; Kummer corroboration |
| 47 | 20 | 17 | 3 | 20 squarefree reductions |
| 53 | 6 | 0 | 6 | 6 squarefree reductions |
| 59 | 18 | 18 | 0 | 15 squarefree reductions, 3 Taylor checks; Kummer corroboration |

## Frozen sequence

1. `protocol.json` fixed the five primes, exact input hashes, the conjugacy map, and 300-second caps before the left producer. `predict_sage.py` factored **only** the left quartic and transported each squarefree factor-degree pattern to the right quartic at `σ(P)`. It retained six repeated reductions as unknown. `predict_attempt.json` records 69.311 seconds and `predictions.json` retains all 68 rows.
2. `fallback_protocol.json` froze those six left places, the first prediction SHA-256, and the exact Kummer certificate before the fallback. `fallback_sage.py` classified them from valuations and quadratic characters of the **left** Kummer radicands; all six resolved. `fallback_attempt.json` records 15.747 seconds. `combine.py` produced 62 reduction-based and six Kummer-based right predictions in `transferred_predictions.json`.
3. `observation_protocol.json` sealed the combined prediction SHA-256 `4029b5c882bac8627cd0fe5aa61fb69b21bb36bbf1ae5a0e7998ae346982979a` **before** right-quartic observation. `observe_sage.py` read that file only for its hash, reconstructed the right quartic separately, and factored its residue polynomial at every base place. `observe_attempt.json` records 62.901 seconds; 62 reductions were squarefree and six remained repeated.
4. `right_kummer_protocol.json` froze the six unresolved right places after the first direct observation. `right_kummer_sage.py` used the **right** Kummer radicands to classify them, recording their valuations, unit residues, and characters. `right_kummer_attempt.json` records 15.442 seconds. `compare.py` verifies all file hashes, exact place identities, methods, and degree patterns. `comparison.json` reports `PASS_ALL_SINGLE_SIDED_TRANSFERS`, 68 matches, with six Kummer-classified rows at that evidence stage.
5. `taylor_protocol.json` separately froze the six repeated right reductions. `taylor_sage.py` lifted each double linear residue root `a`, checked `v_P(g(a))≥2` and `v_P(g'(a))≥1`, and verified the exact normalized reduction `g(a+pz)/p² ≡ Az²+Bz+C (mod P)` with `A=g''(a)/2`, `B=g'(a)/p`, and `C=g(a)/p²`. Every `B²-4AC` was nonzero and square in the degree-two residue field. The two simple roots and split double cluster therefore give four degree-one relative primes at each place. `taylor_attempt.json` records 26.301 seconds. `taylor_audit.py` matches all six Taylor classifications to the sealed predictions and right Kummer results; `taylor_audit_result.json` reports `PASS_ALL_DOUBLE_ROOT_TAYLOR_CHECKS`. `direct_compare.py` uses only the 62 right squarefree reductions and six right Taylor rows as observation evidence; `direct_comparison.json` reports `PASS_ALL_DIRECT_RIGHT_POLYNOMIAL_CHECKS`, 68 matches.

The two Kummer stages share the proven exact conjugacy of their radicands, so their six paired character results are an algebraic cross-check. The Taylor replay is a distinct local calculation from the right quartic coefficients. The 62 squarefree rows and six Taylor rows together provide direct quartic-polynomial checks. Repeated reductions remain explicit in the original stage files.

## Contribution and proof map

For a prime place `P` of the degree-36 base field, the exact identity `g_right = σ(g_left)` transports left factor degrees at `P` to right factor degrees at `σ(P)` when the reductions are squarefree. At the six non-squarefree reductions, the certified biquadratic Kummer presentation determines the unramified local relative degrees from the two unit square characters. The checked Sage code used one left quartic residue factorization per base place: 68 such calls in the prediction stage, compared with 136 calls to directly reduce both quartics at all 68 places. This is an exact call-count reduction, not a measured wall-time speedup.

The structural Lean proof is in the predecessor's `experiments/hecke-432-j1728-quartic-conjugacy-20261026/ConjugateFactors.lean`: `conjugate_quotient_algEquiv`, `conjugate_prime_isPrime`, `conjugate_residue_algEquiv`, and `conjugate_residue_finrank_eq` prove the base-preserving quotient and generic ideal/residue transport. `experiments/hecke-432-j1728-kummer-prime-holdout-20261026/KummerOrbit.lean` proves the four-root orbit rule. The earlier `experiments/hecke-432-j1728-relative-quartic-local-factor-20261026/formal/QuadraticSplit.lean` proves the quadratic discriminant split criterion. Their checked outputs and axiom audits are retained beside those modules. Formalization remains partial at the exact field/coefficient import, integral-closure restriction, and local Hensel/Taylor bridge.

`sage-runtime-info.txt` records the checked local Sage build. Stage times are exploratory local wall times and are not CPU-isolated benchmark results.

## Replay

From the repository root, preserving the frozen protocols and seals:

```sh
python3 experiments/hecke-432-j1728-single-sided-splitting-20261026/run_bounded.py predict
python3 experiments/hecke-432-j1728-single-sided-splitting-20261026/run_bounded.py fallback
python3 experiments/hecke-432-j1728-single-sided-splitting-20261026/combine.py
python3 experiments/hecke-432-j1728-single-sided-splitting-20261026/run_bounded.py observe
python3 experiments/hecke-432-j1728-single-sided-splitting-20261026/run_bounded.py right_kummer
python3 experiments/hecke-432-j1728-single-sided-splitting-20261026/compare.py
python3 experiments/hecke-432-j1728-single-sided-splitting-20261026/run_bounded.py taylor
python3 experiments/hecke-432-j1728-single-sided-splitting-20261026/taylor_audit.py
python3 experiments/hecke-432-j1728-single-sided-splitting-20261026/direct_compare.py
```

Each bounded Sage stage invokes `/Volumes/SSD990/cryptanalysis/sage -python`.
