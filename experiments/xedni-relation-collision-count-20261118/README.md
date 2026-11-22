# Exact collision count from a primitive public relation

**Result.** Let `U=bR` and `V=−aR` generate points in a cyclic subgroup of order `q`. Give each coefficient `u,v` every value in `[-H,H]`, put `L=2H+1`, and assume `gcd(|a|,|b|)=1` and `q>2H(|a|+|b|)`. Then the number of distinct public points `uU+vV` is exactly

```text
L² − max(0,L−|a|) · max(0,L−|b|).
```

This sharpens the `(2H+1)²` upper bound in [the parent experiment](../xedni-bounded-rank-coverage-20261118/README.md). It identifies the collision mechanism of a fixed relation without invoking a rational elliptic point reduction map.

## Mathematical proof

Represent `uU+vV` by the integer `bu−av` modulo `q`. Any two coefficient pairs give integer representatives between `−H(|a|+|b|)` and `H(|a|+|b|)`. Their difference has magnitude at most `2H(|a|+|b|)<q`, so equal residues modulo `q` have equal integer representatives. If `b(u−u′)=a(v−v′)` and `a,b` are coprime, Euclid's lemma gives an integer `t` with `(u−u′,v−v′)=t(a,b)`.

View the `L×L` coefficient grid as a directed graph with an edge from `(u,v)` to `(u+a,v+b)` whenever both vertices are in the grid. Every fiber of `bu−av` is one finite path: the integer values of `t` that keep both coordinates in the box form an interval, and consecutive values give consecutive vertices. There are `L²` vertices and exactly `max(0,L−|a|)max(0,L−|b|)` edges, since each coordinate shift has that many admissible starts. Each path has one more vertex than edges; summing over paths proves the formula.

## Frozen public-panel check

The [protocol](protocol.json) admits all 39 hit-height rows from the independent fresh panel. The [runner](run.py) checks both assumptions separately for every row, computes the closed-form prediction, and compares with the prior exact residue enumeration. [The result](result.json) records **39 assumption passes, 39 matches, and zero mismatches**. The smallest no-wrap margin `q−2H(|a|+|b|)` is 149.

At `H=8`, `L=17`. For the hit `(q,a,b)=(331,4,1)`, the prediction is `289−13·16=81`; for `(419,6,5)`, it is `289−11·12=157`. Both equal the exact public subgroup counts. All 13 `H=8` counts range from 81 to 157.

## Lean proof map

The pinned toolchain is Lean `v4.35.0-rc4`, with Mathlib revision `021c46bdd042f67b538b9f9871d556a93713a9a`. The [Lean source](RelationCollisionCount.lean) has these declarations:

| Step | Declaration | Status |
| --- | --- | --- |
| A public relation gives a one-step coefficient collision | `relation_shift` | Checked |
| Every integer multiple of the relation vector gives a collision | `relation_shift_multiple` | Checked |
| A primitive integer collision is a multiple of the relation vector | `primitive_integer_collision` | Checked |
| Bounded representatives equal if equal modulo a larger modulus | `zmod_no_wrap` | Checked |
| Under primitive and no-wrap hypotheses, two public residues collide exactly when their coefficient difference is a multiple of the relation vector | `zmod_collision_iff_relation_vector` | Checked |
| Every fiber is one path and the edge count gives the displayed cardinality | — | Written proof and 39-row exact check; **Lean formalization partial** |

Run `lake build RelationCollisionCount` to reproduce the module build and the `#print axioms` audit in [build-output.txt](build-output.txt). The outstanding Lean step is a finite-grid path-components/cardinality lemma implementing the final paragraph of the proof; it does not follow from the five structural declarations alone. The module has no `sorry`, `admit`, `sorryAx`, custom research axiom, or unverified native evaluation. `lean4checker --fresh` is unavailable on this host.

Run `python3 run.py` to reproduce the 39-row formula comparison. The runner uses integer arithmetic and existing public data, so it does not invoke Sage.
