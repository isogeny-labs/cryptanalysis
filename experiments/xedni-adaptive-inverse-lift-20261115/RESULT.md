# Adaptive inverse-pair lift: a rational relation on every public inverse event

For integers \(x,y\), set \(B=y^2-x^3+x\) and \(E_{x,y}/\mathbb Q:Y^2=X^3-X+B\). This curve is nonsingular, and its rational points \((x,y)\) and \((x,-y)\) sum to the identity. If \((x,y)\) reduces to a point of \(Y^2=X^3-X-2\) over \(\mathbb F_p\), then \(B\equiv-2\pmod p\), so the chosen rational model reduces to the fixed finite-field model. This constructs a rational \((1,1)\) relation for every admissible reduced pair satisfying the public test \(R_1+R_2=O\).

The discriminant is \(-16(-4+27B^2)\). It is nonzero over \(\mathbb Q\) because no integer \(B\) satisfies \(27B^2=4\). On the eight selected fields, the fixed finite-field curve is nonsingular, so these models also have good reduction at each tested prime.

## Complete ordered-pair census

The frozen query law uses \(Q=17G\), \(R_i=Q-t_iG\), and every ordered \((t_1,t_2)\in[0,q)^2\). The scalar 17 is fixture data used for replay; the producer tests pairs through their public points. Identity and duplicate pairs are recorded before the group-addition test. Every retained group-addition test and every constructed curve is independently replayed by checked Sage in `audit.py`.

| Field prime | Subgroup order \(q\) | Queries \(q^2\) | Admissible group tests | Inverse-pair events | Rational relations |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 313 | 331 | 109,561 | 108,570 | 330 | 330 |
| 421 | 439 | 192,721 | 191,406 | 438 | 438 |
| 431 | 419 | 175,561 | 174,306 | 418 | 418 |
| 547 | 571 | 326,041 | 324,330 | 570 | 570 |
| 571 | 599 | 358,801 | 357,006 | 598 | 598 |
| 593 | 313 | 97,969 | 97,032 | 312 | 312 |
| 617 | 293 | 85,849 | 84,972 | 292 | 292 |
| 677 | 353 | 124,609 | 123,552 | 352 | 352 |
| **Total** | | **1,471,112** | **1,461,174** | **3,310** | **3,310** |

The raw status records also contain 6,628 identity pairs, 3,310 duplicate pairs, and 1,457,864 admissible public nonrelations. There were zero invalid-curve statuses. Each field has exactly \(q-1\) admissible inverse-pair events. The first event in each lexicographic schedule is query 35, \((t_1,t_2)=(0,34)\). For an inverse event, the public equation \(2Q=(t_1+t_2)G\) already supplies the scalar \((t_1+t_2)/2\bmod q\); the recorded replay gives 17. Curve construction occurs *after* that public test and adds no further admissible event. These are operation counts, not wall-time comparisons.

## Proof map and verification

`formal/AdaptiveInverseLift.lean` uses pinned Lean `v4.35.0-rc4` and the Mathlib revision in `formal/lake-manifest.json`.

| Result | Lean declaration | Exact scope |
| --- | --- | --- |
| Integer model casts to the rational model | `rational_model` | All integer \(x,y\) |
| Rational inverse relation and nonsingularity | `inverse_relation` | All integer \(x,y\); the point type requires and receives a proof of nonsingularity |
| Reduction to the fixed finite-field model | `reduction_model` | All \(p,x,y\) satisfying the displayed point equation in `ZMod p` |

Run `cd formal && lake build AdaptiveInverseLift`. The saved build completed 3,156 jobs successfully. The three `#print axioms` reports contain only `propext`, `Classical.choice`, and `Quot.sound` where applicable. No research axiom, `sorry`, or `admit` is used. The Lean declarations prove the rational group relation and the coefficient reduction; the identification of each recorded finite-field input with the resulting point reductions is checked in the independent Sage audit. `lean4checker --fresh` was unavailable on this host.

Run `python3 verify.py` to check the pinned inputs, raw-shard digests and counts, audit, build receipt, and proof report. `SEAL.sha256` fixes the saved packet. The next useful test is a vector-dependent construction whose rational relation is *not* triggered by a directly testable reduced-group identity, with curve search and all failed candidates charged.
