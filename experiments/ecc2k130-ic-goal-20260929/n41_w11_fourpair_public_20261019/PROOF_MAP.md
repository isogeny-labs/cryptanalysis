# Proof map

| Result | Lean declaration and exact hypotheses | Concrete bridge and status |
| --- | --- | --- |
| A raw relation for a Frobenius image of the public point pulls back through inverse Frobenius, preserving base membership and cofactor-four projection | `SixPairTargetOrbit.relation_pullback` in `../n41_sixpair_target_orbit_20261016/OrbitTransport.lean`; arbitrary point type `G`, additive maps `f,g` with `g(f(x))=x`, `g` preserving zero and addition, base closed under `g`, `cofactor(u)=q`, and a finite list relation `sum(points)=f^j(u)` | The theorem is quantified over list length and covers four pair outputs. `audit_result.json` and `w10/audit_result.json` instantiate the point sums and inverse transport in checked Sage. Formalizing the specific binary curve, Frobenius automorphism, and source-base closure in Lean remains open. |
| The W11 and W10 eight-leaf rows use distinct folded columns and project to the public subgroup point | The generic theorem does not encode field arithmetic, source eligibility, or finite-set distinctness | Independent Sage audits verify the concrete statements; `archive_verify.py` independently reconstructs the pair outputs. Full concrete Lean bridges remain open. |
| W9 search covers every one of the 41 chosen target orientations for its fixed source selector | This is a finite native search certificate, not a mathematical theorem | `w9/query_result.json`, hashed input and binary, and `archive_verify.py` record `COMPLETE_NO_HIT` within the resource cap. |

The Lean toolchain is pinned by the reused module's `leanprover/lean4:v4.34.1` proof record. This turn reran:

```sh
elan run leanprover/lean4:v4.34.1 lean experiments/ecc2k130-ic-goal-20260929/n41_sixpair_target_orbit_20261016/OrbitTransport.lean
```

The command exited zero. `lean_check.stdout` records `#print axioms SixPairTargetOrbit.relation_pullback` as `[propext, Quot.sound]`; `lean_check.stderr` is empty. The theorem module contains no `sorry`, `admit`, `sorryAx`, custom research axiom, or native evaluation. `lean4checker --fresh` is unavailable on this host.
