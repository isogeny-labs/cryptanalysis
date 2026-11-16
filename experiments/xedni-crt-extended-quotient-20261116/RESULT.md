# Finite quotients certify every optimized CRT lift test

Every one of the **9,688 selected rational group-test rows** in the archived optimized 13-vector family has a Z-linear independence certificate for its two lifted rational points. The population covers 4,844 tests in each of the centered and shifted CRT lift arms over eight finite fields. This strengthens the parent replay's observed zero rational selected-vector relations: within this fixed population, no nonzero integer coefficient vector can relate either lifted point pair. The parent `(1,2)` rational positive control belongs to a different public vector and remains outside this selected-family population.

## Versioned experiment and exact result

The parent [bounded-prime panel](../xedni-crt-quotient-independence-20261116/RESULT.md) froze primes 3 through 97 and certified 7,887 rows. `protocol.json` here froze all 1,801 unresolved parent rows before a confirming search at primes 101 through 499. Its `result.json` records 1,767 new quotient certificates, three exact rational 2-division-polynomial no-root certificates, and 31 retained torsion-only rows. `protocol-v2.json` then froze those 31 rows and primes 503 through 997; `result-v2.json` records all 31 quotient certificates, with the last first-hit prime 733. Both protocols state the exploratory observations that motivated their ranges without using those observations as final evidence.

| Stage | Input rows needing a certificate | New certified rows | Remaining |
| --- | ---: | ---: | ---: |
| Parent primes 3–97 | 9,688 | 7,887 | 1,801 |
| First extension primes 101–499 and rational 2-division | 1,801 | 1,770 | 31 |
| Second extension primes 503–997 | 31 | 31 | 0 |

Each quotient certificate checks a good integral reduction where the images of P, Q, and P+Q lie outside 2E(F_ℓ). Their classes in E(F_ℓ)/2E(F_ℓ) are independent. A separate odd-order good reduction, or an exact absence of rational roots of the curve's 2-division polynomial, excludes rational 2-torsion. Reducing any proposed integral relation forces both coefficients even; torsion-free halving and infinite descent force both coefficients zero. The archived row identity retains its arm, field, query, vector, curve, and ordered points. Multiple vectors can hit the same pair, so 9,688 counts tests rather than unique pairs.

All 1,801 first-extension rows and all 31 second-extension rows retain attempted-prime statuses, group orders, quotient tests, and first-hit primes. Nonintegral and bad-reduction primes are skipped explicitly. The first run failed before writing a result row because Sage's `prime_range` values were not JSON serializable; `run-initial-failure.json` preserves that producer failure. The corrected source casts those primes to Python integers without changing the frozen mathematical prime law.

## Independent checks and proof map

`audit.py` replays the 1,801 first-extension rows with pure Python general Weierstrass arithmetic and rational-root enumeration. `audit_v2.py` replays the final 31 rows and independently enumerates each finite-field doubled-point set. Both report `PASS`; their receipts are in `audit.json` and `audit-v2.json`. The checked Sage runtime is recorded in `sage-runtime.json`. The parent panel's independent audit covers the first 7,887 certificates and all 9,688 original row identities.

| Mathematical implication | Lean declaration | Status |
| --- | --- | --- |
| Nonzero quotient images force even relation coefficients; no rational 2-torsion gives infinite descent | `independent_of_exponent_two_quotient` in `experiments/xedni-auxiliary-mod2-independence-20261116/AuxiliaryMod2Independence.lean` | checked in stacked PR #1657, pinned build and axiom audit retained there |
| Instantiate on all archived rational curves and reduction maps | no Lean declaration | partial formalization; exact arithmetic certificates and written proof retained across the three versioned panels |

The exact missing Lean bridge is a formal model for the archive's rational elliptic curves, their good-reduction homomorphisms, and kernel checking of the finite-field and rational-root certificates. The abstract theorem preserves the needed hypotheses and does not assume the desired independence. This result concerns the fixed optimized vector family under the two archived CRT lift laws. The next research step is a vector-dependent lift rule fixed before fresh public queries, with its curve-construction rejects and rational tests charged; that would test a different selection mechanism.

## Reproduction

From the repository root, use the checked launcher for both Sage jobs:

```sh
./sage --runtime-info
./sage -python experiments/xedni-crt-extended-quotient-20261116/run.py
python3 experiments/xedni-crt-extended-quotient-20261116/audit.py
./sage -python experiments/xedni-crt-extended-quotient-20261116/run_v2.py
python3 experiments/xedni-crt-extended-quotient-20261116/audit_v2.py
```

`SEAL.sha256` fixes both protocols, sources, raw outputs, summaries, failure receipt, and audits.
