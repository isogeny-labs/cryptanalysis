# Exact rational lifts from known two-point relations

**Every one of the 13 fresh-panel public relations admits an explicit exact rational lift when its coefficient pair is supplied.** For each hit, a good-reduction rational curve and points `P1,P2` were constructed with the prescribed public reductions and `aP1+bP2=O` over `Q`. An independent integer/`Fraction` audit replayed all 13 constructions. Checked Lean theorems derive the common public point from the supplied relation and Bézout inverse, prove the exact lifted group relation, and check the interpolated coefficient congruence.

This establishes a constructive boundary on a proposed universal xedni impossibility statement: exact lifts are possible for known relation coefficients. The construction takes `(a,b)` as input. Finding those coefficients among unknown public points remains the separate relation-discovery problem.

## Construction and written proof

Let `U,V` lie in a prime-order subgroup `C ⊂ E(F_p)` of order `q`, and suppose the supplied integers satisfy `aU+bV=O` with `b` invertible modulo `q`. Compute `R=[b⁻¹ mod q]U`. Then `[b]R=U`; since `[b](V+[a]R)=O` and `[b]` is injective on `C`, `V=[−a]R`.

For the source curve `y²=x³−x−2`, take centered integer representatives `(x,y)` of `R` and set `A=−1`, `B=y²−x³−Ax`. The rational curve `Ẽ: y²=x³+Ax+B` contains the integral point `T=(x,y)`. Because `R` lies on the source curve, `B≡−2 (mod p)`. Its discriminant is nonzero modulo `p`, inherited from the source curve, so `Ẽ` is nonsingular over `Q` and has good reduction at `p`.

Set `P1=[b]T` and `P2=[−a]T`. Good reduction is a group homomorphism, so these reduce to `U,V`, respectively. Their exact rational sum is `[a]P1+[b]P2=[ab−ab]T=O`. This proof uses the supplied relation and invertibility of `b`; it does not require the target scalar used to generate the panel.

[`protocol.json`](protocol.json) froze the 13-hit fresh-panel source digest, all-row admission, construction, checks, and cap before execution. All 13 rows have status `exact_relation`; there are no exclusions or construction failures. The constructed model bit lengths, counting `A,B,x,y`, range from 14 to 25; the maximum bit length across the coordinates of `P1,P2` ranges from 111 to 432. These are exact representation sizes, not timings or a relation-search cost. [`run-result.json`](run-result.json) retains every model, point, reduction witness and status. [`audit-result.json`](audit-result.json) records the independent replay, and [`runtime-info.json`](runtime-info.json) records the accepted Sage build.

## Lean proof map

| Result | Declaration or evidence | Exact hypotheses and status |
| --- | --- | --- |
| A known relation and Bézout inverse give `R=[c]U` with `[b]R=U` and `[−a]R=V` | `XedniKnownRelationLifts.common_point_of_known_relation` in [`KnownRelationLifts.lean`](KnownRelationLifts.lean) | Additive group, `[q]U=[q]V=O`, `[a]U+[b]V=O`, and integer equation `bc+qd=1`; checked |
| Multiples of one lift realize the known two-point relation and reduce to the specified points | `XedniKnownRelationLifts.exact_relation_from_common_lift` in [`KnownRelationLifts.lean`](KnownRelationLifts.lean) | Additive groups, reduction homomorphism, a lift `T`, integers `a,b`, and `b·reduce(T)=U`, `−a·reduce(T)=V`; checked |
| Interpolating the second coefficient preserves its residue | `XedniKnownRelationLifts.interpolated_coefficient_congruence` | Integer on-curve congruence for `x,y,A,B₀`; checked |
| Centered point gives a good-reduction rational curve and integral `T` | Written proof above; [`run.py`](run.py) and [`audit.py`](audit.py) for 13 concrete hits | Elliptic reduction, discriminant preservation, and construction of the rational point are not encoded as Lean terms; formalization partial |

The toolchain is pinned to Lean `v4.35.0-rc4` and Mathlib `021c46bdd042f67b538b9f9871d556a93713a9a9` in [`lean-toolchain`](lean-toolchain), [`lakefile.toml`](lakefile.toml), and [`lake-manifest.json`](lake-manifest.json). [`build-output.txt`](build-output.txt) records `lake build KnownRelationLifts` and `#print axioms`: `propext` for the common-point and congruence theorems; `propext` and `Quot.sound` for the exact-relation theorem. The module contains no `sorry`, `admit`, `sorryAx`, custom axiom, or native-evaluation shortcut. `lean4checker --fresh` was unavailable on this host.

## Reproduction and interpretation

From the repository root:

```sh
./sage --runtime-info > experiments/xedni-known-relation-lifts-20261118/runtime-info.json
./sage -python experiments/xedni-known-relation-lifts-20261118/run.py
python3 experiments/xedni-known-relation-lifts-20261118/audit.py
cd experiments/xedni-known-relation-lifts-20261118 && lake build KnownRelationLifts
```

The audit uses its own modular and rational elliptic-curve addition, checks the source digest and all input rows, reconstructs the curve from `R`, checks good reduction and scalar multiples, and verifies the exact relation and both public reductions. The new constructions depend on the supplied vectors, unlike the previously frozen beam lifts; their representation sizes answer a different question. The next proof or experiment should address **coefficient discovery or a preselected lift rule**, where `(a,b)` is unavailable at construction time.
