# Exact joint residual and prefix proof map

The field is `GF(2)[u]/(u⁴¹+u³+1)` and the curve is
`y²+xy=x³+1`, subgroup order `549756390943`, cofactor four. The
frozen public point is `Q=(1936680952394,910597499030)`. Five W9
source-pair slots have rotations `(0,0,12,12,24)`. Let `Z` be the
sum of the first three signed pair states and let `E₃,E₄` be the
last two signed pair states. If `Z+E₃+E₄=Q`, then group cancellation
gives `Z=(Q−E₄)−E₃`. The circuit's reciprocals are
`w=1/x(Q−E₄)` and `z=1/x(Z)`.

The exact table enumerates all source-signed `E₃,E₄` with disjoint
folded columns, computes `Q−E₄−E₃`, and records the pair `(w,z)`
when its x coordinate is nonzero. All 79,424 column-disjoint pairs in
this instance have a nonidentity residual and nonzero x coordinate.
The low 16 bits of `z` therefore give a necessary condition conditional
on the full 41-bit `w`. The 16-bit BDD asserts this necessary condition
inside the original five-pair XCNF. The original equations and column
constraints remain active.

| Result | Formal or independent check | Status |
| --- | --- | --- |
| Group cancellation gives the first-three-pair residual | `JointResidual.first_three_is_target_residual` | Lean checked, no axioms |
| Any coordinate prefix preserves that necessary equality | `JointResidual.prefix_is_necessary` | Lean checked, no axioms |
| Exact 79,424-row signed support, 1,232 column-collision exclusions, and 2,048 reachable controls | `audit_sage.py`, `audit_result.json` | Independent checked-Sage full enumeration and replay |
| BDD reduction and 16-bit prefix gate | `bdd_screen.py`, `build.py`, `verify.py` | Full 79,424-row acceptance and 2,048-control replay; concrete CNF-to-BDD bridge computational |

The Lean theorems quantify over arbitrary group operations satisfying
associativity, right inverse and right identity, and over arbitrary
coordinate and prefix maps. The concrete elliptic-curve
group and binary field are checked by the full independent Sage replay,
which matched every support row and control. The Lean module does not
formalize the curve coordinates, the 100,081-node BDD, or its emitted
CNF clauses. Those concrete bridges remain partial formalization; the
frozen byte hashes and exhaustive finite controls audit them.

The pinned toolchain is `leanprover/lean4:v4.34.1` in `lean-toolchain`.
`lean JointResidual.lean` succeeded. All three `#print axioms` reports
in `lean.stdout` say that the declarations depend on no axioms.
`lean4checker --fresh` is unavailable in this environment. The first
Lean attempt used a group typeclass absent from this minimal toolchain;
`JointResidual_attempt1.lean` and `lean_attempt1.stderr` retain that
failed build. The revised module states the exact group laws explicitly.

The first Sage audit attempt spent its 180-second cap repeatedly
converting source points. `audit_sage_attempt1.py`,
`audit_protocol_attempt1.json`, and `audit_attempt1.stderr` preserve
that timeout with the original source hash. The retry predecoded
each point once and performed the same full enumeration and control
checks inside its frozen 180-second cap.
