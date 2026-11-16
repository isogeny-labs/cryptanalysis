# Common-preimage lift for arbitrary integer relation vectors

For a prime-order public subgroup on a good-reduction short Weierstrass curve over an odd prime field, every public relation `aU+bV=0` with `b` nonzero modulo the subgroup order has a compatible rational relation with the **same** coefficient vector on an explicitly constructed integral curve. The converse follows by reduction. Thus, when rational curves may vary with the public query and vector, existence of a compatible rational relation is equivalent to the public relation under these hypotheses. This is an existence and construction theorem; finding the public relation and paying for its search remain separate algorithmic work.

The frozen 13-vector panel contains 6,656 distinct query-vector events. Independent public screening found 127 relations. The construction produced a matching rational witness for every one of the 127, with the same `(a,b)` and both point reductions checked. Thirty-two preselected public nonrelation controls also produced rational relations from a common preimage, but their second reductions differed from `V`, as the theorem requires.

## Construction and proof

Let the public subgroup have prime order `q`, and let `b` be invertible modulo `q`. Set `S=b⁻¹U`. From `aU+bV=0` and `U=bS`, cancellation by `b` gives `V=−aS`.

Choose integer coordinates `x,y` lifting `S=(X,Y)` on `E₀/F_p: Y²=X³+A₀X+B₀`, and an integer lift `A` of `A₀`. Define `B=y²−x³−Ax`, `E/Q: y²=x³+Ax+B`, and `T=(x,y)`. The public point equation gives `B≡B₀ mod p`; since `E₀` has good reduction, so does `E`. Set `P=bT` and `R=−aT`. Then

```text
aP+bR = abT−abT = O,
red(P) = bS = U,
red(R) = −aS = V.
```

The rational group relation itself holds for every `T`. Compatibility with both **specified** public points occurs precisely on the selected public relation events. The construction uses public scalar multiplication by the known inverse of `b`; it does not use a target discrete logarithm. For the frozen target-query law `U=Q−t₁G`, `V=Q−t₂G`, a relation gives `(a+b)Q=(at₁+bt₂)G`. All selected events have `a+b` invertible modulo `q`, so the scalar is obtained from the public relation and independently replayed.

## Frozen screen and exact audit

The [protocol](protocol.json) pins the prior [source rows](../xedni-vector-shift-lift-search-20261116/rows.jsonl), field registry, and selected coefficient family by SHA-256. It deduplicates the four prior curve shifts into 6,656 ordered query-vector events, screens every event, constructs all 127 public relation events, and selects the first four nonrelation events per field as 32 negative controls. All exceptions, mismatches, and attempted lifts remain rows.

| Recorded item | Count |
| --- | ---: |
| Distinct query-vector events screened | 6,656 |
| Public relations | 127 |
| Matching rational witnesses with original `(a,b)` | 127 |
| Nonrelation controls with nonmatching second reduction | 32 |
| Construction or audit failures | 0 |
| Offset-derived scalar replays | 127 |

The 127 public events by field are `p=47:24`, `101:11`, `191:20`, `211:15`, `251:13`, `281:8`, `347:19`, and `349:17`. The [screen](screen.jsonl) and [lift rows](lifts.jsonl) preserve all ordered inputs and constructed rational coordinates. The runner used the checked repository Sage launcher after saving [runtime information](sage-runtime.json). An [independent Python audit](audit.py) reconstructed all 6,656 finite relations and all 159 selected rational lifts with separate finite and rational group laws; [audit.json](audit.json) records `PASS`.

A [post hoc coordinate-size diagnostic](height-diagnostic.json) records the maximum numerator or denominator bit length among the two rational points: for the 127 matching witnesses, median 214 bits, range 9–405 bits. These are exact representation sizes on this bounded panel, not a cost comparison. The construction does not imply that searching for a public relation is easy or that a resulting rational witness is small under a prescribed height cap.

## Formal proof map

The pinned Lean 4 `v4.35.0-rc4` and Mathlib revision `021c46bdd042f67b538b9f9871d556a93713a9a9` build [CommonPreimageLift.lean](formal/CommonPreimageLift.lean):

| Declaration | Checked scope |
| --- | --- |
| `common_preimage_relation_lift` | For arbitrary additive commutative groups and reduction homomorphism, a witness `T` reducing to `S`, `bS=U`, injective multiplication by `b` on the public group, and `aU+bV=0` construct `P,R` with both required reductions and `aP+bR=0`. |
| `public_relation_of_compatible_lift` | Any compatible rational relation maps to the same-vector public relation. |
| `one_point_curve_lift` | The integral coefficient formula places the lifted point on its new curve over any commutative ring. |
| `one_point_coefficient_reduces` | The constructed coefficient reduces to the public coefficient under the public point equation. |

The [build output](formal/build-output.txt) records `#print axioms`: the common-preimage theorem uses `[propext, Quot.sound]`; the other three use `[propext]`. No research axiom or unproved placeholder appears. The remaining concrete formal bridge is a Mathlib elliptic-curve model of good reduction and scalar-multiplication compatibility, together with the elementary proof that `b mod q ≠ 0` makes multiplication by `b` injective on the stated prime-order subgroup. The checked group theorem retains those requirements explicitly, and the Sage/Python audits instantiate them on all frozen cases.

The next proof and measurement step is to fix a height bound and a source-independent curve selection rule, then measure whether any relation-search algorithm gains information before it has effectively found the public relation. This tests the computational part of the proposed calculus while preserving the exact input law and every failed or capped attempt.
