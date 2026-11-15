# Exact selection-law control for a bounded relation

Selection from six rational points changes the fixed relation event by a
factor of `50/3` compared with the corresponding uniform reduced-point law.
For the frozen ordered, pairwise-distinct, nonidentity triples on
`E/Q: y²+y=x³−x`, reduction at 127 gives:

| Law on ordered triples | Tuples | Relation `x₁+x₂−x₃=O` | Event fraction |
| --- | ---: | ---: | ---: |
| Selected rational lifts `mP`, `m∈{-3,-2,-1,1,2,3}` | 120 | 16 | `2/15` |
| Uniform distinct nonidentity points in `E(F₁₂₇)` | 1,953,000 | 15,624 | `1/125` |

The chosen `P=(0,0)` reduces to a generator of the prime-order group
`E(F₁₂₇)`, whose order is 127. The selected rational points remain distinct
and nonidentity after reduction. The program checks every selected relation
over both `Q` and `F₁₂₇`, and exhausts the full uniform ordered-triple law.
The uniform count also follows directly: `(q−1)(q−2)(q−3)` admissible
triples and `(q−1)(q−3)` relation triples for odd prime `q`, giving
`1/(q−2)` at `q=127`.

For fixed `s=(1,2,3)` and `w=7`, the xedni sample map
`xᵢ=sᵢw−tᵢ` is checked on all 120 selected triples; it has 120 distinct
preimages under this selected law. That map preserves the event count when
the law is transported through it. The selected support has pointwise density
`1,953,000/120 = 16,275` relative to the uniform distinct-point law, while
this particular event is enriched by `50/3`.

This control fixes one rank-one rational curve and chooses its multiples as
lifts. It quantifies why an exact uniform event bound needs a selection-law
factor before application to a rational-lift procedure. The original xedni
construction instead varies the rational curve and applies auxiliary modular
conditions; measuring that procedure requires its own frozen candidate and
acceptance rule. The conditional weight theorem in the selection-law Lean
module (PR #1559) is the formal bridge for such a rule.

The protocol and predictions were saved before the checked Sage run. To
reproduce from the repository root:

```sh
./sage --runtime-info > experiments/xedni-selection-bias-control-20261115/sage-runtime-info.json
./sage -python experiments/xedni-selection-bias-control-20261115/run.py > experiments/xedni-selection-bias-control-20261115/result.json 2> experiments/xedni-selection-bias-control-20261115/run.stderr
python3 experiments/xedni-selection-bias-control-20261115/audit.py
```

The Sage run exited zero with empty stderr. `audit.py` independently recounts
the selected integer triples, checks the uniform formula and exact fractions,
and validates the protocol, source and runtime hashes. The runtime receipt
records the accepted Sage source and native binary manifest.
