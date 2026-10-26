# Level-432 modular-map construction probe

The lower-conductor lift `E: y²=x³−16` has an exact level-432 newform and a computable modular-parametrization `q`-series. Checked Sage produced coefficients through the **Sturm bound 144** and Laurent series for the map; an independent checked-Sage replay matched all 145 saved newform coefficients and verified both the curve equation and the differential identity through `q³⁹`. The resulting data is a reproducible starting point for an algebraic `X₀(432) → E` map.

| Constructed object | Leading terms or result | Verification |
| --- | --- | --- |
| Weight-two newform | `q + q⁷ + 5q¹³ + 7q¹⁹ − 5q²⁵ + 4q³¹ + 11q³⁷ + …` | exact coefficients `q⁰` through `q¹⁴⁴` replayed |
| Map `X(q)` | `q⁻² + 2q⁴ + q¹⁰ + 4q¹⁶ + …` | `Y²=X³−16` through `q³⁹` |
| Map `Y(q)` | `−q⁻³ + 5q³ + 5q⁹ + 9q¹⁵ + …` | `X′/(2Y)=f(q)/q` through `q³⁹` |
| Bounded eta screen | 665 candidates; zero matches through `q³⁹` | independent exponent census and binomial-series replay |

The [protocol](protocol.json) fixed the exact model, level, precisions, and eta family before the persisted runs. The [Sage producer](qseries_result.json) records all coefficients, the level index `864`, Sturm bound `144`, and diagnostic phase times. The [independent Sage audit](qseries_validation.json) rebuilds every coefficient and both truncated identities from the installed parametrization implementation.

The eta screen considers products `∏ η(dz)^r` with `d | 432`, at most three nonzero exponents, `|r| ≤ 8`, `∑r=4` (weight two), and `∑dr=24` (leading term `q`). It records the second modularity congruence for each candidate but does not need it for rejection: even the broader formal-series family has no match through `q³⁹`. The best candidates match through `q¹²` and first differ at `q¹³`. The [complete screen ledger](eta_result.json) retains all 665 factor sets and first differences; [independent replay](eta_validation.json) uses a separate brute-force enumeration and binomial expansion. This screen does not cover eta quotients with four or more supported divisors, larger exponents, or linear combinations.

Sage's installed `ModularParameterization` exposes upper-half-plane complex evaluation and Laurent `q`-series; these outputs are not an algebraic evaluator on `X₀(432)(F_p)`. The next construction should recover an explicit function-field model or modular-function coordinates for `X₀(432)`, express `X` and `Y` in that field, and then test exact finite-field evaluation and rational-preimage frequency on frozen secp256k1 points. The present status is an exact `q`-series and bounded-description stage, with `candidate_id: null` and no online timing result.

Reproduce from `/Volumes/SSD990/cryptanalysis` with the checked Sage launcher:

```sh
./sage --runtime-info > experiments/hecke-432-qseries-20261025/sage_runtime.json
./sage -python experiments/hecke-432-qseries-20261025/produce_sage.py
python3 experiments/hecke-432-qseries-20261025/screen_eta.py
./sage -python experiments/hecke-432-qseries-20261025/verify_sage.py
python3 experiments/hecke-432-qseries-20261025/verify_eta.py
```
