# Rank-one coordinate cover bound for xedni lifts

A rank-one lift rule that covers every element of a subgroup of order `q` with one rational generator, `T` torsion labels, and integer coordinate `|k|≤K` must satisfy

`q ≤ T(2K+1)`.

The pinned Lean theorem `torsion_coordinate_cover_lower_bound` proves this for any generator image `g : ZMod q` and any torsion-label map `Fin T → ZMod q`: the represented elements are the image of a set with exactly `T(2K+1)` members. No elliptic-curve rank, independence, or distribution premise is hidden in this count. The theorem `no_uniform_rank_one_cover_with_torsion` combines it with the proposed rank-gap hypotheses `K≤cL`, `T(2c+1)<L`, and `(4L+1)^2−1<q` to derive a contradiction. The corresponding torsion-free declarations are also checked.

## Frozen larger-order panel

At `L=4,c=1,K=4,T=1`, the rank-gap left side is `3<4`, and the two-point reduced witness box has `17²−1=288` vectors. Each selected subgroup order exceeds 288. Yet the rank-one coordinate interval has only `2K+1=9` positions. The table is exact arithmetic on the pinned selection result, paired with the earlier checked-Sage centered-coordinate control.

| Field prime | Subgroup order `q` | Cover capacity | At least this many residues uncovered | Measured centered sum radius `K` |
| ---: | ---: | ---: | ---: | ---: |
| 313 | 331 | 9 | 322 | 1,320 |
| 421 | 439 | 9 | 430 | 1,752 |
| 431 | 419 | 9 | 410 | 1,672 |
| 547 | 571 | 9 | 562 | 2,280 |
| 571 | 599 | 9 | 590 | 2,392 |
| 593 | 313 | 9 | 304 | 2,496 |
| 617 | 293 | 9 | 284 | 1,168 |
| 677 | 353 | 9 | 344 | 1,408 |

These measured radii belong to the earlier centered lift policy. The new theorem rules out **every** globally covering rank-one policy with the displayed small-coordinate premise, including other coordinate selection rules. It does not rule out a policy that admits only selected public inputs, uses larger coordinates, has higher free rank, or changes the representation group with each input. Those policies require their own admission count, coordinate bound, and selection law.

## Proof and reproduction

| Result | Lean declaration | Hypotheses |
| --- | --- | --- |
| One generator requires `q≤2K+1` | `coordinate_cover_lower_bound` | Every `z:ZMod q` has a representative `k•g` with `|k|≤K` |
| Torsion labels require `q≤T(2K+1)` | `torsion_coordinate_cover_lower_bound` | Every `z` has a representative `k•g+torsion(t)` with `|k|≤K` |
| Rank-gap inequalities contradict full coverage | `no_uniform_rank_one_cover`, `no_uniform_rank_one_cover_with_torsion` | The cover hypothesis and the exact inequalities stated above |

The formal package pins Lean `v4.35.0-rc4` and Mathlib `021c46bdd042f67b538b9f9871d556a93713a9a9`. Run `cd formal && lake build RankOneCover`; the saved build completes 3,138 jobs. Each `#print axioms` lists only `propext`, `Classical.choice`, and `Quot.sound`. The module has no `sorry`, `admit`, custom research axioms, or unverified native proof step. `lean4checker --fresh` was unavailable on this host.

`protocol.json` pins the two parent result hashes and the numeric gate before `run.py` evaluates it. Run `python3 run.py` from this directory, then `python3 verify.py`; the latter checks all hashes, exact rows, the Lean build receipt, and the seal. The next arithmetic step is to establish coordinate-cover or selected-input lower bounds for higher-rank or variable-curve lift families.
