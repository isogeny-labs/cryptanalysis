import Mathlib.Data.Finset.Basic
namespace M31Projection

theorem queried_intersection {X : Type*} [DecidableEq X] (queried triples quads : Finset X)
    (covered : triples ⊆ queried) :
    triples ∩ (quads ∩ queried) = triples ∩ quads := by
  ext x
  simp only [Finset.mem_inter]
  exact ⟨fun h => ⟨h.1,h.2.1⟩,fun h => ⟨h.1,h.2,covered h.1⟩⟩

end M31Projection
