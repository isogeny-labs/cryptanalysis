# Constructive integral lift of public doubling relations

Every nonidentity public point `U=(X,Y)` with `Y≠0` on a good-reduction short Weierstrass curve has an integral curve lift on which a lifted point doubles to a rational point reducing to `2U`. Thus every selected public relation `2U=V` in the frozen fresh-query panel admits an explicitly constructed rational relation `2P=R` on a curve varying with `U`. All 512 query events were constructed and independently checked: ten reductions matched the archived second public point `V`, exactly the ten public doubling-relation events; 502 reduced to a different second public point.

## Construction and proof

Let the public curve over `F_p` be `Y²=X³+A₀X+B₀`, with `p` odd and good reduction. Choose integer lifts `x,y` of `X,Y`, and an integer lift `s` of the public tangent slope `(3X²+A₀)/(2Y)`. Define

```text
A = 2ys − 3x²                  B = y² − x³ − Ax
u = s² − 2x                   v = s(x−u) − y.
```

Then `P=(x,y)` and `R=(u,v)` lie on `E: y²=x³+Ax+B`; the tangent formula on `E` gives `2P=R`. The identities hold over the integers. Modulo `p`, the slope and point equations give `A≡A₀` and `B≡B₀`, so `E` has the specified good reduction and `P` reduces to `U`. The doubling formula gives `R mod p=2U`. If a proposed public second point `V` satisfies `2U=V`, both lifts match it. The construction does not need the scalar used to generate the target fixture or the archived `V` coordinates to choose `E` and `R`; it uses `U`, the public curve, and the deterministic centered lift convention.

This also explains the sharp difference between the previous four-shift search and existence: that restricted search found one exact rational relation among its ten public doubling events, whereas the tangent construction reaches all ten. Once `2U=V` is known, the query offsets already give `Q=(2t₁−t₂)G`; building the rational lift does not supply an additional relation event. The remaining algorithmic question is how to obtain useful public relations and account for that work, not whether this doubling-shaped event has some compatible rational model.

## Frozen experiment

The [protocol](protocol.json) pins the prior [candidate rows](../xedni-vector-shift-lift-search-20261116/rows.jsonl) by SHA-256 `3c75b8f6aed964b99e3135cda848289669f7f6bf54a7a8c603ec37b9198e5b9e`. It takes the first row for each of the 512 distinct field-target-query events under the previously selected `(2,-1)` vector. No event is dropped for an exceptional lift. The [constructor](construct.py) writes one row per event, including the rational curve, lifted points, second-point reduction, status, and offset-derived scalar where applicable.

| Event | Count |
| --- | ---: |
| Frozen public query events | 512 |
| Integral rational curves and points constructed | 512 |
| Rational `2P=R` reducing to archived `2U=V` | 10 |
| Rational `2P=R` reducing to `2U≠V` | 502 |
| Singular, bad-reduction, or undefined-slope events | 0 |
| Matching scalar replays | 10 |

The ten matching events occur at `p=47` (3), `251` (2), `281` (1), `347` (3), and `349` (1). [rows.jsonl](rows.jsonl) retains every construction and [result.json](result.json) retains the exact counts and hashes. The [independent Sage audit](audit_sage.py), launched through `/Volumes/SSD990/cryptanalysis/sage` after saving [runtime information](sage-runtime.json), reconstructs the finite target and both query points from the pinned generator, builds every rational curve and point, checks `2P=R`, checks both reductions and good reduction, and replays all ten offset-derived scalars. [audit-sage.json](audit-sage.json) records `PASS`. This is an exact construction and correctness panel without a wall-time comparison.

## Formal proof map

The pinned Lean 4 `v4.35.0-rc4` and Mathlib revision `021c46bdd042f67b538b9f9871d556a93713a9a9` build [ConstructiveDoublingLift.lean](formal/ConstructiveDoublingLift.lean):

| Declaration | Checked statement |
| --- | --- |
| `constructed_doubling_coordinates` | The formulas place both constructed points on one short Weierstrass curve, give the tangent numerator identity, and satisfy the exact square condition, over any commutative ring. |
| `constructed_coefficients_reduce` | Under the public point equation and tangent-slope equation, the constructed coefficients equal the public coefficients in any commutative ring, including `F_p`. |

The [build output](formal/build-output.txt) records `#print axioms` as `[propext, Quot.sound]` and `[propext]`, respectively. The group-law bridge from these polynomial coordinates to `2P=R` in Mathlib's nonsingular elliptic-curve point group remains to be formalized, with `Y≠0`, odd characteristic, and good reduction stated explicitly. Sage independently checked that group-law statement on every frozen event.

The next experiment should vary the public relation shape, starting with `mP=R` for `m=3`, and derive coordinate constructions with explicit coefficient, degree, and height costs. A useful comparison would hold the same public query law and count the work required to find each public relation before constructing its rational lift.
