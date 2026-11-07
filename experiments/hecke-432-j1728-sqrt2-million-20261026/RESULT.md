# Million-cap classification of the source-`j=1728` level-432 C–E branch

The exact √2 conjugate-factor reduction gate certifies absence of rational C–E pairs at 9,799 of the 9,809 primes `7 ≤ p < 1,000,000` with `p ≡ 11 (mod 24)`. Direct finite-field enumeration classifies the ten exceptional cells. Six exceptional primes have rational C–E pairs: `11, 131, 227, 1523, 148139, 182339`. The frozen inverse B-branch formula yields four valid C–E–B triples, all at `p=131`; every pair at the other five positive cells has a zero branch denominator.

| Interval | Prime cells | Norm-certified good | Direct exceptions | Rational C–E pairs at exceptions | Valid C–E–B triples |
| --- | ---: | ---: | ---: | ---: | ---: |
| `7 ≤ p < 20,000` | 283 | 275 | 8 | 10 | 4 |
| `20,000 ≤ p < 1,000,000` | 9,526 | 9,524 | 2 | 4, two at each exception | 0 |
| Complete frozen cap | 9,809 | 9,799 | 10 | 14 | 4 total, at `p=131` |

The new exceptions are `148139` and `182339`. Each divides the numerator of the exact octic conjugate-pair resultant norm. At each prime there are two rational source-`j=1728` C points, one rational `x_E` root across them, and two E points over that root. Their C–E pairs all have `ZERO_DENOMINATOR` under the frozen inverse B branch. [`exception_result.json`](exception_result.json) retains the actual points and per-pair classifications.

## Frozen inputs and computation

The exact denominator LCM and six rational norms were established in the [preceding bounded result](../hecke-432-j1728-sqrt2-resultants-20261026/RESULT.md). For a prime passing this sufficient gate, both conjugate factor pairs remain coprime after reduction, and coefficient Frobenius exchanges their `√2` components because `(2/p)=-1`. A rational resolvent root would be fixed by Frobenius and therefore a common root of one conjugate pair, contradicting coprimality. The [Lean Frobenius-swap proof](../hecke-432-j1728-sqrt2-split-20261026/formal/FrobeniusSwapGate.lean) checks this structural step; the [two-pair product lemma](../hecke-432-j1728-sqrt2-resultants-20261026/formal/BoundedGate.lean) checks its combination with a nonzero unit.

[`protocol.json`](protocol.json) pins the exact norm gate and prior 20,000-cap result by SHA-256 and fixes the one-million exclusive cap. A preliminary read-only scan of `20,000 ≤ p < 100,000` found no new exception; the one-million cap was frozen before running [`scan.py`](scan.py). Its [`result.json`](result.json) records all ten gate exceptions and the 9,799 certified cells. [`audit_scan.py`](audit_scan.py) independently enumerates primes with a byte sieve, repeats the modular integer arithmetic, and checks the complete exception list; [`audit_result.json`](audit_result.json) has status `PASS_INDEPENDENT_MILLION_CAP_SIEVE_AND_EXCEPTION_AUDIT`.

[`exception_protocol.json`](exception_protocol.json) froze the two newly identified primes and the coordinate, resolvent, inverse-filter, and branch-formula input hashes before direct enumeration. [`audit_new_exceptions.py`](audit_new_exceptions.py) iterates every field `x_C`, reconstructs the source `y_C` values, evaluates the source-j rational function, then tests every `x_E` against the degree-12 resolvent and both `y_E` values where present. It applies the recorded branch implementation to every rational pair. The output status is `EXACT_DIRECT_NEW_EXCEPTION_CLASSIFICATION`.

For independent replay, [`sage_replay_protocol.json`](sage_replay_protocol.json) pins the direct result and characteristic-zero degree-18 field certificate. [`replay_new_exceptions_sage.py`](replay_new_exceptions_sage.py) finds the source roots by finite-field polynomial factorization, reconstructs `y_C` from the exact rational formula, solves the specialized resolvent with Sage's polynomial roots, checks the E equation, and evaluates the branch denominator directly. It reproduces the full pair sets with status `PASS_INDEPENDENT_SAGE_NEW_EXCEPTION_REPLAY`. The run used the repository's checked `./sage` launcher; [`sage-runtime-info.txt`](sage-runtime-info.txt) records the installed runtime.

## Proof map and next arithmetic step

| Claim component | Declaration or executable check | Verification |
| --- | --- | --- |
| Frobenius-fixed roots excluded by swapped coprime factors | `J1728Sqrt2Split.no_fixed_root_of_swapped_coprime_factors` | Lean checked in predecessor |
| Product of two excluded pairs and nonzero unit has no root | `J1728BoundedGate.no_root_of_two_excluded_pairs` | Lean checked in predecessor |
| 9,809-cell prime screen and exact divisibility | `scan.py`, independent `audit_scan.py` | Exact integer/sieve checks passed |
| Two new exceptional finite-field cells | `audit_new_exceptions.py`, independent `replay_new_exceptions_sage.py` | Exhaustive enumeration and Sage polynomial replay passed |

The numerical reduction of the explicit degree-18/36 coefficient arrays and the finite-field enumerations are certificate checked; a faithful Lean encoding of these large concrete arrays and all 9,809 prime cells remains open. The exact octic resultant norm contains factors at the two new exceptional primes. A next step is to factor its remaining integer cofactor or prove a valuation criterion that identifies all exceptional primes without a finite cap.
