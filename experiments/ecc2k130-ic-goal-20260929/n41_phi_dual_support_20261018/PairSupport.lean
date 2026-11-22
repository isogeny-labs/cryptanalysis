import Std
import Init.Grind.Ring.Basic

namespace PairSupport
open Lean.Grind

def pairSums {G : Type} [Add G] (left right : List G) : List G :=
  left.flatMap (fun a => right.map (fun b => a + b))

/-- Enumerating the Cartesian product of two point domains preserves every
    finite group sum from those domains. -/
theorem complete {G : Type} [Add G] (left right : List G)
    (a b : G) (ha : a ∈ left) (hb : b ∈ right) :
    a + b ∈ pairSums left right := by
  apply List.mem_flatMap.mpr
  exact ⟨a, ha, List.mem_map.mpr ⟨b, hb, rfl⟩⟩

/-- Each enumerated pair sum has an input pair witness. -/
theorem sound {G : Type} [Add G] (left right : List G) (z : G)
    (hz : z ∈ pairSums left right) :
    ∃ a ∈ left, ∃ b ∈ right, z = a + b := by
  obtain ⟨a, ha, hm⟩ := List.mem_flatMap.mp hz
  obtain ⟨b, hb, heq⟩ := List.mem_map.mp hm
  exact ⟨a, ha, b, hb, heq.symm⟩

#print axioms complete
#print axioms sound

end PairSupport
