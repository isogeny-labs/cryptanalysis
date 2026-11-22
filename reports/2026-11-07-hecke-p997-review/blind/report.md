# Independent blind arithmetic review: T-1791

Reviewer: `/root/p997_blind_algebra`  
Review date: 2026-11-07  
Disposition: **all five supplied assertions hold**. Each of the three requested alterations breaks its corresponding conclusion.

The only research input read was
`/var/tmp/cryptanalysis-p997-review-20261107/reports/2026-11-07-hecke-p997-review/blind-input.md`.
Its SHA-256 is
`4f46b7c9675eb35cfff1b42eed67baef4b16255b1687dbc68283eecaea4359f9`.
The parent supplied the revision identifier `639fb3de7`. I did not inspect Git or independently verify the file-to-revision binding, because the blind-review instruction excluded Git history and other repository paths. No producer proof, source, archived result, sibling output, external reference, or memory was read.

Natural numbers are interpreted as nonnegative integers, including zero. Natural subtraction means `x - y = max(x-y,0)` where the subtraction inside `max` is integer subtraction.

## Assertion 1: the capped maximum sum is rigid — holds

**Statement.** If `a,b,c <= 24` and `a+b+c=72`, then `a=b=c=24`.

**Derivation.** Define nonnegative integer deficits
`d_a=24-a`, `d_b=24-b`, `d_c=24-c`. The caps guarantee that these are ordinary nonnegative differences. Their sum is

```text
d_a+d_b+d_c = 72-(a+b+c) = 0.
```

A sum of nonnegative integers is zero only when every summand is zero. Hence all three deficits are zero, giving `a=b=c=24`. Conversely, `(24,24,24)` satisfies the hypotheses. It is the unique eligible tuple.

**Requested negative control at sum 71 — breaks.** The tuple `(23,24,24)` meets the caps and sums to 71, while the claimed equality fails. In fact the deficits then sum to one, so the complete list of eligible tuples and counterexamples is

```text
(23,24,24), (24,23,24), (24,24,23).
```

## Assertion 2: sum 12 forces an interior coordinate — holds

**Statement.** If `a+b+c=12`, at least one coordinate lies strictly between 0 and 24.

**Derivation.** The positive sum guarantees at least one positive coordinate; call it `x`. Nonnegativity of the other two gives `x <= a+b+c = 12`. Therefore `0 < x <= 12 < 24`, as required. For example, `(12,0,0)` satisfies the hypothesis and has an interior coordinate.

**Requested negative control at sum zero — breaks.** Nonnegative coordinates summing to zero must all be zero. The unique eligible tuple is `(0,0,0)`, and none of its coordinates is strictly positive. This is an exact counterexample to the altered assertion.

The original conclusion cannot be strengthened to require all three coordinates to be interior: `(12,0,0)` disproves that stronger statement.

## Assertion 3: capped sum 48 forces two positive coordinates — holds

**Statement.** If `a,b,c <= 24` and `a+b+c=48`, at least two coordinates are positive.

**Derivation.** Suppose at most one coordinate were positive. The other two would be zero, and the possible positive coordinate would be at most 24 by its cap. Thus `a+b+c <= 24`, contradicting `a+b+c=48`. Consequently at least two are positive.

The tuples `(24,24,0)`, `(24,0,24)`, and `(0,24,24)` show that exactly two positive coordinates can occur. They are the only such eligible tuples: with one coordinate zero, the remaining two sum to 48 and are each at most 24, forcing both to equal 24. Thus the conclusion cannot be strengthened to require three positive coordinates.

**Requested negative control without the cap — breaks.** The tuple `(48,0,0)` is a natural-number tuple with sum 48 and only one positive coordinate. The complete counterexample list is

```text
(48,0,0), (0,48,0), (0,0,48).
```

Completeness follows because the sum is positive, so an offending tuple has exactly one positive coordinate, and that coordinate must equal 48.

## Assertion 4: the weighted sum is 78 — holds

**Statement.** `6*1 + 60*1 + 6*2 = 78`.

**Derivation.** The three products are `6`, `60`, and `12`. Therefore the sum is `6+60+12=66+12=78`.

## Assertion 5: the stated natural-subtraction bounds hold — holds

**Statement.** If `79 <= F <= 217`, then `791 <= 1008-F <= 929` using natural-number subtraction.

**Derivation.** The hypothesis gives `F <= 217 < 1008`, so natural subtraction does not truncate in this range. Subtraction from 1008 reverses the inequalities:

```text
1008-217 <= 1008-F <= 1008-79,
       791 <= 1008-F <= 929.
```

Both bounds are attained. The exact endpoint pairs `(F,1008-F)` are `(217,791)` and `(79,929)`.

As additional boundary controls, weakening the lower hypothesis to allow `F=78` gives `(F,1008-F)=(78,930)`, violating the upper conclusion. Weakening the upper hypothesis to allow `F=218` gives `(218,790)`, violating the lower conclusion. Thus both input endpoints are sharp for this fixed output interval.

## Independent finite verification

The independently written `check_arithmetic.py` ran successfully with:

```sh
python3 -I -S /var/tmp/p997-blind-review-output/check_arithmetic.py
```

Its exit code was zero. It constructs natural-number triples directly from the fixed sums, applies the stated caps where relevant, and checks every eligible case. It also evaluates natural subtraction as `max(a-b,0)`. All program assertions passed, and `verification.json` records the results.

| Check | Eligible inputs | Failure or counterexample count |
| --- | ---: | ---: |
| A1, sum 72 with cap 24 | 1 triple | 0 |
| A2, sum 12 | 91 triples | 0 |
| A3, sum 48 with cap 24 | 325 triples | 0 |
| A4, literal arithmetic | 1 expression | 0 |
| A5, integer `F` from 79 through 217 inclusive | 139 values | 0 |
| A1 changed to sum 71 with cap 24 | 3 triples | 3 counterexamples |
| A3 with cap removed, sum 48 | 1,225 triples | 3 counterexamples |
| A2 changed to sum zero | 1 triple | 1 counterexample |

The case counts also follow directly: natural triples of sum 12 number `C(14,2)=91`; capped triples of sum 48 correspond bijectively to nonnegative deficits summing to 24 and number `C(26,2)=325`; uncapped triples of sum 48 number `C(50,2)=1225`. For the deficit count, every deficit is automatically at most 24 because all are nonnegative and their sum is 24.

These are arithmetic conclusions about the supplied hypotheses. Whether the hypotheses describe a concrete geometric census was explicitly assigned to a separate source review and is unassessed here.

## Artifacts and attestation

All reviewer-created artifacts are outside the repository, in `/var/tmp/p997-blind-review-output/`:

- `report.md`: this report, with independent derivations and exact counterexamples.
- `review_attestation.json`: source-access and per-claim attestation.
- `check_arithmetic.py`: independent exhaustive verifier.
- `verification.json`: verifier output.

No repository file was modified. No sibling was contacted or accessed.
