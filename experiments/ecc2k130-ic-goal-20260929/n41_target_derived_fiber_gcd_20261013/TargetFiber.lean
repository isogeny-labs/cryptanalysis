import Std

/- Composition of exact upper-root enumeration with an exact product-fiber
   membership oracle. The curve-law, polynomial-root, and GCD bridges are
   separate obligations recorded in PROOF_MAP.md. -/

namespace TargetFiber

variable {K : Type} [Zero K]

def query (leftRoots : List K) (targetRoots : K → List K)
    (fiberHit : K → Prop) : Prop :=
  ∃ z ∈ leftRoots, ∃ v ∈ targetRoots z, fiberHit v

theorem query_iff_exists_source_witness
    (leftRoots : List K) (targetRoots : K → List K)
    (fiberHit : K → Prop) (upper : K → K → K → K)
    (H : K → K → K → K) (target : K)
    (firstProducts secondProducts : List K)
    (rootExact : ∀ z v, v ∈ targetRoots z ↔ upper z v target = 0)
    (fiberExact : ∀ v, fiberHit v ↔
      ∃ p ∈ firstProducts, ∃ q ∈ secondProducts, H p q v = 0) :
    query leftRoots targetRoots fiberHit ↔
      ∃ z ∈ leftRoots, ∃ v, upper z v target = 0 ∧
        ∃ p ∈ firstProducts, ∃ q ∈ secondProducts, H p q v = 0 := by
  constructor
  · rintro ⟨z, hz, v, hv, hh⟩
    exact ⟨z, hz, v, (rootExact z v).mp hv, (fiberExact v).mp hh⟩
  · rintro ⟨z, hz, v, hu, hpq⟩
    exact ⟨z, hz, v, (rootExact z v).mpr hu, (fiberExact v).mpr hpq⟩

#print axioms TargetFiber.query_iff_exists_source_witness

end TargetFiber
