# Varying-curve xedni selection census

The deterministic two-point lift census reconstructs a rational short
Weierstrass curve through each admissible pair on
`E/F₄₇: y²=x³−x−2`. With the paper's one-step weaker reverse-Mestre
condition at 7, the accepted reduced relation event is `2/20`, compared
with `42/1722` in the full ordered point-pair law: an exact enrichment of
`41/10`. The 20 accepted ordered pairs comprise 10 unordered pairs on three
reconstructed rational curves. Neither accepted relation pair satisfies
`Q₁+2Q₂=O` on its rational curve.

The auxiliary prime gives an explicit certificate for both rejected rational
relations. Their accepted reconstructed curve reduces at 7 to
`y²=x³+6`; the lifted points reduce to `Q₁=(4,0)` and `Q₂=(1,0)`.
Here `2Q₂=O`, so `Q₁+2Q₂=(4,0)≠O` modulo 7. The two ordered input pairs
are sign mirrors and give the same local certificate.

| Frozen census arm | Ordered pairs | Reduced `P₁+2P₂=O` | Rational `Q₁+2Q₂=O` |
| --- | ---: | ---: | ---: |
| Full distinct nonidentity input law | 1,722 | 42 | 2 |
| Strict auxiliary gate, `#E(F₇)=3` | 0 | 0 | 0 |
| Weak auxiliary gate, `#E(F₇)=4` | 20 | 2 | 0 |

The frozen second-prime extension tests those same 20 pairs at 11 without
changing their rational coefficients. The curves for all 20 pairs have good reduction at
11; 16 pairs retain rank-two incidence rows. Their curve orders are 8
(four rows), 12 (eight), and 14 (eight). Thus the strict reverse-Mestre
order 6 and the `ε=1` order 7 each accept zero pairs. The two pairs with
the reduced relation at 47 also satisfy that relation modulo 11, so the
second-prime exclusion comes from its required curve order. `protocol-v3.json`
freezes both order arms and the SHA-256 of the prior 20-pair input before
this extension was run.

The finite-field curve has 43 points, all in its prime-order group. The
`42/1722 = 1/41` reduced event rate is also exact by group counting: for
each nonidentity second point, `P₁=-2P₂` gives one distinct nonidentity
first point. Every input point is lifted by the centered integer coordinate
representative in `[-23,23]`. When the two lifted x-coordinates differ,
the two rational equations uniquely determine `A,B` in
`y²=x³+A*x+B`. The run checks that the resulting curve is nonsingular,
passes through both points over `Q`, and reduces to the fixed curve at 47.

The strict gate was frozen and run first. Its raw rows record 24 pairs whose reconstructed curves have
`#E(F₇)=4`, 20 of which also have rank-two incidence rows. None has the
strict required order 3. `protocol-v2.json` preserves the amendment to order
4, corresponding to the paper's `ε=1` weak reverse-Mestre alternative.
Both arms require coefficients integral at 7, good reduction, and rank-two
point-incidence rows there. The two rational relations in the full pool
belong to a curve with bad reduction at 7 and are rejected by both gates.

This experiment implements the two-point simplified lift with a unique
short-Weierstrass reconstruction and one auxiliary prime. The original
[xedni algorithm](https://pages.cpsc.ucalgary.ca/~jacobs/PDF/xedni.pdf)
allows more curve coefficients, CRT conditions across several primes, and
curve optimization. The exact 1,722-pair census therefore measures this
specified selection rule. The second-prime extension keeps the original
coefficients; a full CRT coefficient-choice policy can move to other
rational curves through the same lifted points. That policy is the next
experiment, with the same reduced-event and rational-relation accounting.

The complete per-pair rows, including failed construction and gate statuses,
are in `rows.jsonl.gz` and `rows-v2.jsonl.gz`, compressed in Git under the
repository data-file limit. Their uncompressed SHA-256 values remain in the
result records. The independent `audit.py` checks
the receipt hashes, reconstructs every rational curve coefficient,
recomputes finite-field and rational group relations, recounts the auxiliary
curve orders and incidence ranks, checks the local obstruction, and checks both result summaries. It
passed for all 3,444 saved rows. Both checked Sage runs exited zero with
empty stderr. Runtime receipts pin the accepted Sage source and native
binary manifest.

`rows-v3.jsonl` retains all 20 second-prime outcomes, including the four
rank failures and both zero-yield order arms. A separate checked Sage replay
recomputes all 20 curve orders, point-incidence ranks and local group
relations at 11; `audit.py` validates its source and runtime receipts.

Reproduce from the repository root using the checked launcher:

```sh
./sage --runtime-info > experiments/xedni-varying-curve-selection-20261115/sage-runtime-info-v2.json
./sage -python experiments/xedni-varying-curve-selection-20261115/run_v2.py > experiments/xedni-varying-curve-selection-20261115/result-v2.json 2> experiments/xedni-varying-curve-selection-20261115/run-v2.stderr
python3 experiments/xedni-varying-curve-selection-20261115/run_v3.py > experiments/xedni-varying-curve-selection-20261115/result-v3.json 2> experiments/xedni-varying-curve-selection-20261115/run-v3.stderr
./sage --runtime-info > experiments/xedni-varying-curve-selection-20261115/sage-runtime-info-v3.json
./sage -python experiments/xedni-varying-curve-selection-20261115/sage_audit_v3.py > experiments/xedni-varying-curve-selection-20261115/sage-audit-v3.json 2> experiments/xedni-varying-curve-selection-20261115/sage-audit-v3.stderr
python3 experiments/xedni-varying-curve-selection-20261115/audit.py
```
