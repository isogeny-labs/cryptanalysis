# Level-432 C–E resolvent factor parity at `j=1728`

The exact C–E resolvent exhibits a reproducible factor-parity split on the tested `j=1728` fibers. The first prospective rule, based only on `p mod 12`, failed at two primes and exposed a finer `p mod 24` distinction. A second, frozen rule passed at nine fresh selected primes: at `p ≡ 23 (mod 24)`, each selected C point had four linear and four quadratic resolvent factors; at `p ≡ 11 (mod 24)` and the sampled ordinary `p ≡ 1 (mod 12)` fibers, every factor had even degree. The repository Sage build independently replayed all 126 factorized polynomials in both tests.

## Frozen inputs and selection

The factor is the degree-12 polynomial in `x_E` from the [relative resolvent](../hecke-432-relative-resolvent-20261025/relative_resolvent.json), evaluated at rational points on `C: y²+y=x³−7` whose source `j` is 1728. Prime selection uses the [exact degree-18 x-eliminant](../hecke-432-j1728-cubic-twist-holdout-20261026/elimination_result.json) and the [source `j` coordinate map](../hecke-27-coordinate-bridge-20261025/coordinate_map.json); it does not read the C–E resolvent. Input hashes, bounds, selection rules, predictions, and preserved zero cells are in [`protocol.json`](protocol.json) and [`refined_protocol.json`](refined_protocol.json). Both scripts select ascending primes under their fixed caps before their respective factor tests.

The initial diagnostic [`factor_sample.py`](factor_sample.py) used the earlier passing primes 1319, 1367, 1439 and ordinary primes 1753, 2917, 3037 to formulate the first prediction. Their per-C patterns were `(1,1,1,1,2,2,2,2)` in the former group and all-even patterns in the latter. This sample is exploratory and appears in [`factor_sample.json`](factor_sample.json).

## First prospective test: failed prediction retained

[`select_primes.py`](select_primes.py) froze nine primes from `5000 ≤ p < 10000`: the first three `p ≡ 1 (mod 12)` with at least 18 rational source C points, the first three `p ≡ 11 (mod 12)` with at least two, and the first three `p ≡ 5 (mod 12)` regardless of C count. Its 50 examined cells are in [`selection.json`](selection.json). The first prediction expected the `11 mod 12` class to inherit the earlier four-linear pattern. [`test_prediction.py`](test_prediction.py) preserved the two failures in [`test_result.json`](test_result.json).

| Class and primes | C points per prime | C–E factor pattern per C point | Rational C–E pairs per prime | Prediction |
| --- | ---: | --- | ---: | --- |
| `1 mod 12`: 6397, 6577, 6637 | 18 | all even degree: six quadratics or two quadratics and two quartics | 0 | passed |
| `5 mod 12`: 5009, 5021, 5081 | 0 | no C fiber | 0 | passed |
| `11 mod 12`: 5003, 5051 | 2 | six quadratics | 0 | **failed** |
| `11 mod 12`: 5039 | 2 | four linears and four quadratics | 8 | passed |

The two failed primes are `11 mod 24`; the passing prime is `23 mod 24`. The first test status is `FAIL_PROSPECTIVE_FACTOR_PARITY` and remains part of the record.

## Refined prospective test: nine fresh primes

After seeing the first failure, [`refined_protocol.json`](refined_protocol.json) fixed a new prediction and a disjoint scan from `7000 ≤ p < 20000`: three `23 mod 24` primes with at least two C points, three `11 mod 24` primes with at least two, and three ordinary `1 mod 12` primes with at least 18. [`select_refined.py`](select_refined.py) selected them from 29 source-only cells. [`test_refined.py`](test_refined.py) then evaluated the C–E factors. The status in [`refined_test_result.json`](refined_test_result.json) is `PASS_REFINED_FACTOR_PARITY`.

| Selected class | Primes | C points per prime | Factor degrees per C point | Rational C–E pairs per prime |
| --- | --- | ---: | --- | ---: |
| `23 mod 24` | 7079, 7103, 7127 | 2 | `1,1,1,1,2,2,2,2` | 8 |
| `11 mod 24` | 7019, 7043, 7187 | 2 | `2,2,2,2,2,2` | 0 |
| `1 mod 12` | 7129, 7237, 7717 | 18 | `2,2,2,2,2,2` or `2,2,4,4` | 0 |

The `1 mod 12` row includes both `1 mod 24` (7129) and `13 mod 24` (7237, 7717). The degree patterns are exact factorizations of the specialized polynomial, while the rational-pair counts also require the E-curve equation `y_E²=x_E³+432` at each linear root. Every root, factor degree, C point, prime, and status is retained in the JSON records.

## Independent replay and next proof step

[`audit_sage.py`](audit_sage.py) rebuilds each specialized polynomial from the frozen resolvent terms in the repository's checked Sage runtime, verifies the C equation and source `j`, refactors over `GF(p)`, checks each linear root and multiplicity, and counts rational E points. It passed all 126 rows: 60 from the failed first protocol and 66 from the refined one. The runtime receipt is [`sage-runtime-info.txt`](sage-runtime-info.txt), and the audit receipt is [`audit_sage.json`](audit_sage.json).

The next mathematical step is to factor the level-16 correspondence over the source-`j=1728` CM field and identify the involution or quadratic character whose Frobenius value controls odd-degree factors. The observed `p mod 24` rule is a finite-field hypothesis with a successful fresh-prime test; the original `p mod 12` rule is falsified. A faithful Lean statement becomes appropriate once that structural bridge is established. This remains a stage diagnostic with `candidate_id: null`; it supplies an arithmetic gate for later source-chain comparisons rather than a complete IC pipeline.
