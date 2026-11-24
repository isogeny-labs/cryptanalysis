import Mathlib.Data.List.Sort
namespace M31MirrorOrder

abbrev p := 2147483647

/-- Sorted lower representatives expand to a sorted list of both signs. -/
theorem ordered (xs : List Nat) (sorted : xs.Pairwise (· ≤ ·))
    (lower : ∀ x ∈ xs, 2*x < p) :
    (xs ++ (xs.reverse.map (fun x => p-x))).Pairwise (· ≤ ·) := by
  apply List.pairwise_append.mpr
  refine ⟨sorted, ?_, ?_⟩
  · apply List.pairwise_map.mpr
    apply List.pairwise_reverse.mpr
    exact sorted.imp (fun {_ _} h => Nat.sub_le_sub_left h p)
  · intro x hx y hy
    obtain ⟨z,hz,rfl⟩ := List.mem_map.mp hy
    have a := lower x hx
    have b := lower z (List.mem_reverse.mp hz)
    omega

end M31MirrorOrder
