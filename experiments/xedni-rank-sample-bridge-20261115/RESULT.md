# A checked rank-to-sample bridge for xedni lifts

`XedniRankSampleBridge.selected_rank_gap_sample_count` composes the finite rank-gap witness with the selected-sample obstruction. Fix a prime subgroup order `q`, a radius `L` with `2L<q`, an admitted sample set `A`, and a complete finite list `S` of nontrivial integer relation vectors bounded by `2L`. If every dependent admitted lift has a rank-`d` lattice representation with `d<r`, coordinate radius `K<=cL`, and a torsion list satisfying `T(2c+1)^d<L`, then

`|{t in A : the compatible selected lift at t is dependent}| * q <= |S| * q^r`.

The proof obtains a bounded relation from the rank-and-torsion value count for each dependent admitted tuple. It then uses reduction compatibility and the fixed candidate list to apply the exact finite-field sample count. The rank, basis, torsion list, and coordinate radius may depend on the admitted sample; `L` and the candidate list are fixed before sampling. The bounded witness is a theorem conclusion, not a separately assumed principle.

## Proof map and hypotheses

| Result | Lean declaration | Exact hypotheses |
| --- | --- | --- |
| Selected rank-gap event count | `selected_rank_gap_sample_count` | Prime `q`; `2L<q`; compatible lifts on `A`; every dependent admitted tuple has a representation by a `d<r` coordinate lattice and listed torsion with `K<=cL` and `T(2c+1)^d<L`; complete fixed candidate list `S` |

The module imports exact copies of `XedniObstruction.lean` from PR #1554 commit `03525133f5b6f5110ad1ab1322d1ee9eec9f54a6` and `HeightPigeonhole.lean` from PR #1560 commit `2ac7ee29f73bdaad8c9571eac158c81dd72e1498`. Source hashes and commit identities are pinned in `DEPENDENCIES.json`. The imported theorems respectively provide the selected finite-field count and the explicit rank-gap bounded relation.

The next arithmetic step is to establish the dependent-tuple representation and its uniform radius for the paper's selected elliptic-curve lift family from canonical heights, regulator or basis-free geometry, torsion, discriminant, and Lang assumptions. The theorem is an absolute sample count. A conditional probability for a particular selection law uses its admitted-set size or sample weights, as developed in the separate weighted extension.

Lean `v4.35.0-rc4` and Mathlib `021c46bdd042f67b538b9f9871d556a93713a9a9` are pinned. `lake build RankSampleBridge` passed, and the saved `#print axioms` record for the new theorem uses `propext`, `Classical.choice`, and `Quot.sound`. The 16 imported sampling and nine imported rank declarations have the same standard-foundation audit. `verify.py` seals source and output hashes and checks all 26 records. `lean4checker --fresh` was unavailable on this host.
