# Raw cofactor image proof map

| Result | Declaration or check | Exact scope | Status |
| --- | --- | --- | --- |
| Additive projection of `P+tau(P)` doubles the projected component when that component is Frobenius fixed | `CofactorImage.projected_image_doubles` | Any additive commutative group, an additive projection on this pair, and a fixed projected Frobenius point | Lean 4.34.1 kernel checked; `#print axioms` reports no axioms |
| An order-four source class maps into classes zero or two | `CofactorImage.image_class_even` | Four explicit source classes and `2T+2T=0`, under the preceding additive/fixed hypotheses | Lean 4.34.1 kernel checked; `#print axioms` reports standard `propext` only |
| The ECC2K-130 rational curve has the four torsion points used here, Frobenius fixes them, and `[r]` gives the class coordinate | `census.py` and `audit_sage.py` | Exact N131 model, `r=680564733841876926932320129493409985129`, official four-lift fiber | Computational replay; full Lean curve/group-law bridge remains open |
| Exact d13 source and image class counts | `census.py`, `audit_sage.py` | Every valid selector in the frozen d13 subspace, with both signs | Exact finite census; independent Sage replay status in `audit_result.json` |
| Ten-position torsion-class tuple counts | `analyze.py` | Ordered independent source choices in distinct Frobenius positions, each with the same class counts | Exact integer convolution; uniform occupancy within each size-`r` coset is a separate heuristic |

The readable group argument is: `E(F_{2^131})` has order `4r`, and the four
official raw lifts differ by the rational four-torsion subgroup. Let `T4`
generate that subgroup. Since every rational torsion point is Frobenius fixed,
`[r](P+tau(P))=[r]P+tau([r]P)=2[r]P`. As `r=1 (mod 4)`, `[r]P` is the
cofactor class coordinate in `Z/4`. Doubling sends classes `0,1,2,3` to
`0,2,0,2`. The full Lean bridge from the concrete characteristic-two curve,
its rational-point group, and the supplied target fiber to these abstract
group hypotheses remains to be formalized. The exact enumerated counts are
retained as computational certificates rather than encoded as Lean axioms.

Build: `lean CofactorImage.lean` from this directory. The pinned toolchain is
`leanprover/lean4:v4.34.1`; `lean.stdout` records the two axiom audits.
`lean4checker --fresh` is unavailable on this host.
