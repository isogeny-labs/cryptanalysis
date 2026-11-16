# Selected rational-lift height panel at p = 47

The frozen centered-lift selection law admits 20 ordered pairs on three rational elliptic curves. Their 40 selected points have positive computed canonical height. The observed maximum-to-minimum selected-height ratios are 1.15234, 1.16647, and 1.26154. A checked Lean theorem shows why each ratio is a lower bound for the corresponding ratio using the curve's least positive rational-point height, provided that minimum exists and is positive. The numerical ratios use Sage's 128-bit height approximation; an independent 192-bit replay agreed within 1e-30 for every selected point.

## Method and result

The parent `xedni-varying-curve-selection-20261115` v2 census fixes E(F_47): y²=x³−x−2, all 1,722 ordered distinct nonidentity pairs, centered integer coordinate lifts, the unique rational short Weierstrass curve through each eligible pair, and one auxiliary weak reverse-Mestre gate at 7. This experiment inherits every archived admission status and measures every accepted row, regardless of its reduced relation status. The exact parent gzip SHA-256 is in `protocol.json`; `audit.py` checks all 1,722 rows against the parent and independently replays all 40 heights.

| Rational model (A, B) | Ordered accepted rows | Rank arm | Selected min height m | Selected max height M | M/m, approximate | Model discriminant |
| --- | ---: | --- | ---: | ---: | ---: | ---: |
| (-1129, -13679) | 4 | rank 3, complete | 2.6363648854 | 3.0379988842 | 1.1523438584 | 11266762384 |
| (-847, 8035) | 8 | rank 3, complete | 2.7412103127 | 3.1975509858 | 1.1664741560 | 10998857872 |
| (-9478/31, 64516/31) | 8 | timeout at 30 s | 3.7875646434 | 4.7781829311 | 1.2615449190 | -1250046381824/29791 |

The rank arm used `rank(proof=True)` and `gens(proof=True)` on each curve in a separate checked-Sage process, capped at 30 seconds per curve. Its stdout, stderr, return code, and timeout state are in `rank-results.json`. The reported discriminants belong to the displayed models; no minimal-model discriminant is inferred. The first two completed rank arms are diagnostic and do not alone certify the global minimum positive height.

## Height-ratio implication and proof map

Write μ_E for the least strictly positive Néron–Tate height of a rational point on the same E(Q), if it exists. For any positive observed selected height m and maximum M≥0, μ_E≤m implies M/m≤M/μ_E. This is the entire structural bridge used here; the experiment does not compute μ_E. The displayed decimal ratios inherit the numerical height precision and are not interval-certified mathematical constants.

| Result | Lean declaration | Hypotheses | Status |
| --- | --- | --- | --- |
| Selected ratio lower bound | `selected_height_ratio_lower_bound` in `SelectedLiftHeightBound.lean` | real μ>0, μ≤m, M≥0 | checked |

Toolchain: `leanprover/lean4:v4.35.0-rc4`, Mathlib revision `021c46bdd042f67b538b9f9871d556a93713a9a9`. Command: `lake build SelectedLiftHeightBound`; `build-output.txt` records 9,040 completed jobs and `#print axioms` reports only `propext`, `Classical.choice`, and `Quot.sound`. `lean4checker --fresh` was unavailable. The readable proof is division by positive denominators followed by μ≤m and M≥0.

The next step is a certified lower bound for μ_E on these selected curves, or a frozen larger CRT/optimization selection law that yields a materially different height distribution. The present panel fixes one auxiliary prime and does not sample those later stages.

## Reproduction

From the repository root, run the checked launcher:

```sh
./sage --runtime-info
./sage -python experiments/xedni-selected-lift-height-panel-20261116/run.py
./sage -python experiments/xedni-selected-lift-height-panel-20261116/audit.py
python3 experiments/xedni-selected-lift-height-panel-20261116/rank_panel.py
```

`sage-runtime.json` preserves the accepted local build receipt. `rows.jsonl.gz`, `result.json`, `audit.json`, and `rank-results.json` preserve all observed and censored rows. `SEAL.sha256` fixes the final artifacts.
