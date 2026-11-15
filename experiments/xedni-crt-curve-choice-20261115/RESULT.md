# CRT curve choice for two-point xedni lifts

A deterministic CRT choice in the monic Weierstrass family constructs rational
curves meeting the frozen auxiliary orders at 7 and 11 for 1,344 of the
1,722 ordered point pairs on `E/F₄₇: y²=x³−x−2`. The accepted set contains
34 pairs with the reduced relation `P₁+2P₂=O`; two sign-related pairs also
satisfy `Q₁+2Q₂=O` on their reconstructed rational curves. The accepted
pairs occupy 672 distinct rational curves. This supplies an explicit
small-field rational-lift relation within the stated deterministic policy.

| Frozen arm | Input pairs | Accepted rational curves by pair | Reduced relation in accepted pairs | Rational relation in accepted pairs |
| --- | ---: | ---: | ---: | ---: |
| Full ordered distinct nonidentity `E(F₄₇)` law | 1,722 | — | 42 | — |
| One free coefficient `a₂` | 1,722 | 0 | 0 | 0 |
| Free `a₁,a₂,a₃` with CRT | 1,722 | 1,344 | 34 | 2 |

The base curve has prime group order 43. Its full reduced relation rate is
`42/1722 = 1/41`. The full-family accepted rate is `34/1344 = 17/672`, an
event enrichment of `697/672` relative to the full law. The rational
relation rate within accepted pairs is `2/1344 = 1/672`. The two rational
relation pairs are sign-related and share one underlying curve shape; these
finite-panel fractions are exact counts, not independent-trial estimates.

One checked witness uses the rational curve with Weierstrass coefficients
`[a₁,a₂,a₃,a₄,a₆]=[-987,-1034,0,7660,-3997]` and lifted points
`Q₁=(14,7)`, `Q₂=(17,10)`. The Sage run and an independent exact-rational
doubling audit check `Q₁+2Q₂=O`. Its reductions at 47 are the same affine
points and satisfy the same relation. Its reductions at 7 and 11 have 4 and
6 points respectively. The sign-related witness has `a₁=987` and negated
y-coordinates.

## Construction and boundary

For each pair, center the finite-field affine coordinates in `[-23,23]`.
At 7, search free coefficients `(a₁,a₂,a₃)` by increasing centered size for
the first nonsingular curve of order 4 through the two reduced lifted
points. At 11, seek order 6 first, then order 7. Combine each free
coefficient with the required zero residue at 47 by CRT modulo 3,619.
Solve the two rational point equations for `a₄,a₆`. The selected rational
curve must be nonsingular and reduce to the prescribed curve at all three
primes. The source checks the full incidence rank, curve orders, point
equations and group relations. The coefficient and arm choice is fixed in
`protocol-v2.json` before the full-family census.

The first frozen arm held `a₁=a₃=0` and varied only `a₂`. Its 1,722-row
census found 88 pairs with an order-4 candidate at 7, but none of those
pairs had an order-6 or order-7 candidate at 11. That arm and its zero-yield
rows remain in `protocol.json`, `run.py` and `rows.jsonl`. The widened family
accepts every pair whose lifted x-coordinates differ modulo 47, 7 and 11:
42 pairs fail the first check, 224 the second and 112 the third. It uses
the strict order-6 arm at 11 for every accepted pair; the frozen order-7
fallback has zero selected rows.

This implements a two-point coefficient CRT choice in one monic
Weierstrass family. The [original xedni algorithm](https://pages.cpsc.ucalgary.ca/~jacobs/PDF/xedni.pdf)
also allows auxiliary point CRT, more curve coefficients, and discriminant
optimization. The finite witness demonstrates that a universal
impossibility statement would be false; the relevant next mathematical
question is a bounded-probability theorem for the actual selection law and
height conditions as the field grows. The previously checked conditional reduction
and sampling theorems in the existing Lean modules apply only with their
stated bounded-witness and sampling hypotheses.

`PROOF_MAP.md` records the existing abstract reduction theorem, the exact
Sage/arithmetic witness, and the open faithful Lean elliptic-curve
formalization. The current shared checkout failed its existing Lean source
hash verifier, so this PR does not report a fresh checked Lean build.

## Reproduction

The protocol and input law were frozen before each arm. The initial run of
the restricted arm stopped at JSON serialization before any pair row was
written. Its source, stderr and empty row file are retained as
`run-failed.py`, `run-failed.stderr` and `rows-failed.jsonl`; the corrected
run and full-family run both exited zero with empty stderr. Runtime receipts
record the accepted Sage source and native binary manifest.

```sh
./sage --runtime-info > experiments/xedni-crt-curve-choice-20261115/sage-runtime-info.json
./sage -python experiments/xedni-crt-curve-choice-20261115/run.py > experiments/xedni-crt-curve-choice-20261115/result.json 2> experiments/xedni-crt-curve-choice-20261115/run.stderr
./sage --runtime-info > experiments/xedni-crt-curve-choice-20261115/sage-runtime-info-v2.json
./sage -python experiments/xedni-crt-curve-choice-20261115/run_v2.py > experiments/xedni-crt-curve-choice-20261115/result-v2.json 2> experiments/xedni-crt-curve-choice-20261115/run-v2.stderr
python3 experiments/xedni-crt-curve-choice-20261115/audit.py
```

The large raw row streams are committed as `rows.jsonl.gz` and
`rows-v2.jsonl.gz` under the repository data-file limit; the result records
retain their uncompressed SHA-256 values. The independent `audit.py` checks
both source and runtime receipts, all
1,722 input pairs, every accepted curve equation and finite-field order,
the reduced group relation, and the rational relation by an exact doubling
formula. It preserves all failed construction statuses and checks the
two rational witnesses. `SEAL.sha256` seals the complete artifact set.
