import Mathlib.Tactic

namespace M31.ResidueFilter

/-- Address in the 16,384-word bitmap indexed by the low twenty bits. -/
def address (k : ℕ) : ℕ × ℕ := (k % 1048576 / 64, k % 64)

theorem bounds (k : ℕ) : (address k).1 < 16384 ∧ (address k).2 < 64 := by
  unfold address
  omega

theorem filtered_count (keys : List ℕ) (k : ℕ) :
    (if address k ∈ keys.map address then keys.count k else 0) = keys.count k := by
  split_ifs with h
  · rfl
  · have absent : k ∉ keys := fun hk => h (List.mem_map_of_mem hk)
    exact (List.count_eq_zero_of_not_mem absent).symm

end M31.ResidueFilter
