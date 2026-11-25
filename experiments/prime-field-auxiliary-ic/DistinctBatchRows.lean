import Std

namespace DistinctBatchRows

variable {α : Type} [DecidableEq α]

theorem lookup_bound (p : α) (xs : List α) (h : xs.Nodup) :
    xs.count p ≤ 1 := by
  induction xs with
  | nil => simp
  | cons x xs ih =>
    obtain ⟨fresh, tail⟩ := List.nodup_cons.mp h
    by_cases same : x = p
    · subst x
      simp [List.count_eq_zero_of_not_mem fresh]
    · simpa [List.count_cons, same, Ne.symm same] using ih tail

/-- Each suffix contributes its number of occurrences of its first point. -/
def diagonalMatches : List α → Nat
  | [] => 0
  | x :: xs => (x :: xs).count x + diagonalMatches xs

theorem diagonal_exact (xs : List α) (h : xs.Nodup) :
    diagonalMatches xs = xs.length := by
  induction xs with
  | nil => rfl
  | cons x xs ih =>
    obtain ⟨fresh, tail⟩ := List.nodup_cons.mp h
    simp [diagonalMatches, List.count_eq_zero_of_not_mem fresh, ih tail, Nat.add_comm]

def suffixSlots : Nat → Nat
  | 0 => 0
  | n + 1 => n + 1 + suffixSlots n

theorem twice_slots (n : Nat) : 2 * suffixSlots n = n * (n + 1) := by
  induction n with
  | zero => rfl
  | succ n ih => simp only [suffixSlots, Nat.mul_add, ih, Nat.add_mul]; omega

theorem thousand_point_rows (xs : List α) (h : xs.Nodup) (size : xs.length = 1000) :
    diagonalMatches xs = 1000 ∧ suffixSlots xs.length = 500500 := by
  refine ⟨(diagonal_exact xs h).trans size, ?_⟩
  have count := twice_slots xs.length
  rw [size] at count ⊢
  omega

end DistinctBatchRows
