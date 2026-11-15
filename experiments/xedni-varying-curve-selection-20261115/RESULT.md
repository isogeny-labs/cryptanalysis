# Varying-curve xedni selection census

The deterministic two-point lift census reconstructs a rational short
Weierstrass curve through each admissible pair on
`E/F₄₇: y²=x³−x−2`. With the paper's one-step weaker reverse-Mestre
condition at 7, the accepted reduced relation event is `2/20`, compared
with `42/1722` in the full ordered point-pair law: an exact enrichment of
`41/10`. The 20 accepted ordered pairs comprise 10 unordered pairs on three
reconstructed rational curves. Neither accepted relation pair satisfies
`Q₁+2Q₂=O` on its rational curve.

| Frozen census arm | Ordered pairs | Reduced `P₁+2P₂=O` | Rational `Q₁+2Q₂=O` |
| --- | ---: | ---: | ---: |
| Full distinct nonidentity input law | 1,722 | 42 | 2 |
| Strict auxiliary gate, `#E(F₇)=3` | 0 | 0 | 0 |
| Weak auxiliary gate, `#E(F₇)=4` | 20 | 2 | 0 |

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
specified selection rule. Its next falsifier is to add a second auxiliary
prime and an explicit coefficient-choice policy, then repeat the same
reduced-event and rational-relation accounting.

The complete per-pair rows, including failed construction and gate statuses,
are in `rows.jsonl` and `rows-v2.jsonl`. The independent `audit.py` verifies
the receipt hashes, reconstructs every rational curve coefficient,
recomputes finite-field and rational group relations, recounts the auxiliary
curve orders and incidence ranks, and checks both result summaries. It
passed for all 3,444 saved rows. Both checked Sage runs exited zero with
empty stderr. Runtime receipts pin the accepted Sage source and native
binary manifest.

Reproduce from the repository root using the checked launcher:

```sh
./sage --runtime-info > experiments/xedni-varying-curve-selection-20261115/sage-runtime-info-v2.json
./sage -python experiments/xedni-varying-curve-selection-20261115/run_v2.py > experiments/xedni-varying-curve-selection-20261115/result-v2.json 2> experiments/xedni-varying-curve-selection-20261115/run-v2.stderr
python3 experiments/xedni-varying-curve-selection-20261115/audit.py
```
