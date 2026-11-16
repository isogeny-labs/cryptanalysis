# Finite quotients certify 7,887 optimized CRT lift tests

The fixed small-prime criterion certifies Z-linear independence of the two lifted rational points in **7,887 of 9,688** archived selected rational group-test rows (81.41%) across the centered and shifted CRT laws. Each certificate combines independent images in E(F_ℓ)/2E(F_ℓ) with an odd-order good reduction at an odd prime, which excludes rational 2-torsion. The other 1,801 rows remain explicitly unclassified by this prime range: 1,798 have only the no-2-torsion certificate, and three have only a quotient certificate. The parent optimized-family replay recorded zero rational selected-vector relations in all 9,688 tests; this experiment supplies a structural certificate for most of those rows rather than relying on the zero count alone.

## Frozen population and result

`protocol.json` pins the parent protocol, result, and seal hashes; the runner checks all 16 input JSONL hashes and the 9,688-row count before processing. The population consists of 4,844 tests in each lift arm, across fields 47, 101, 191, 211, 251, 281, 347, and 349. A test row fixes its target query, public relation vector, rational curve, and ordered lifted pair. Multiple vectors can occur on the same curve and point pair, so these are test-row counts, not a count of distinct rational curves or point pairs. All parent failed auxiliary construction probes remain charged in the parent archive; this diagnostic reuses its accepted tests.

| Base field p | Tests per arm | Centered certified | Shifted certified | Centered other states | Shifted other states |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 47 | 436 | 346 | 364 | 90 torsion only | 72 torsion only |
| 101 | 558 | 446 | 450 | 112 torsion only | 108 torsion only |
| 191 | 556 | 461 | 441 | 94 torsion only, 1 quotient only | 115 torsion only |
| 211 | 818 | 670 | 678 | 148 torsion only | 140 torsion only |
| 251 | 586 | 501 | 489 | 85 torsion only | 97 torsion only |
| 281 | 728 | 608 | 591 | 120 torsion only | 137 torsion only |
| 347 | 468 | 367 | 369 | 101 torsion only | 99 torsion only |
| 349 | 694 | 556 | 550 | 136 torsion only, 2 quotient only | 144 torsion only |
| **Total** | **4,844** | **3,955** | **3,932** | **886 torsion only, 3 quotient only** | **912 torsion only** |

The ordered search covers primes 3 through 97 listed explicitly in `protocol.json`, with a 900-second cap; the run completed all rows before the cap. For each row, `rows/<arm>-p<field>-tests.jsonl` retains every prime status until both certificates are found or the list is exhausted. Nonintegral and bad-reduction primes are recorded and skipped. An odd group order at a good odd prime rules out rational 2-torsion by injectivity of reduction on 2-torsion. For the quotient test, the exact condition is that P, Q, and P+Q are all outside the doubled-point set 2E(F_ℓ). This makes their quotient classes independent. The absence of rational 2-torsion then gives infinite descent on the even coefficients of any rational relation.

The independent `audit.py` performed 90,595 finite-model evaluations after file-local caching, using Python's general Weierstrass group law and exact point enumeration. It compared every archived input identity, every attempted-prime status, group order, doubling-set test, first certificate prime, output hash, and aggregate count; `audit.json` records `PASS`. This audit uses no Sage elliptic-curve group routines. The checked Sage runtime receipt is in `sage-runtime.json`.

## Proof map and next step

The structural implication is the checked Lean declaration `independent_of_exponent_two_quotient` in `experiments/xedni-auxiliary-mod2-independence-20261116/AuxiliaryMod2Independence.lean`, inherited through the stacked parent PR #1657. Its exact hypotheses are an additive group with no 2-torsion, a homomorphism to an exponent-2 quotient, and nonzero images of P, Q, and P+Q. The pinned Lean build and `#print axioms` receipts are in that experiment. The curve-specific instantiation remains a **partial formalization**: formal models of these rational elliptic curves, good-reduction homomorphisms, and 9,688 arithmetic certificates have not been constructed in Lean. The written proof, exact inputs, and independent arithmetic verifier are retained here.

The next experiment should test the 1,798 torsion-only rows at a larger frozen prime range and examine whether their lifted pairs are already dependent modulo 2 in E(Q)/2E(Q). The three quotient-only rows admit a separate exact rational 2-division-polynomial check. A missing certificate in this bounded search is a coverage state, not an assertion of rational dependence.

## Reproduction

From the repository root:

```sh
./sage --runtime-info
./sage -python experiments/xedni-crt-quotient-independence-20261116/run.py
python3 experiments/xedni-crt-quotient-independence-20261116/audit.py
```

`SEAL.sha256` fixes the protocol, source, raw rows, summaries, and receipts.
