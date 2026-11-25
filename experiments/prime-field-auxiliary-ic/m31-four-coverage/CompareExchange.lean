import Mathlib.Data.Nat.Basic
import Init.Data.Array.Perm

namespace M31Comparator

structure Gate where
  left : Nat
  right : Nat
  ascending : Bool

def exchange (g : Gate) (xs : Array Nat) : Array Nat :=
  if hi : g.left < xs.size then
    if hj : g.right < xs.size then
      if (if g.ascending then xs[g.left] > xs[g.right] else xs[g.left] < xs[g.right])
      then xs.swap g.left g.right else xs
    else xs
  else xs

theorem exchange_perm (g : Gate) (xs : Array Nat) : (exchange g xs).Perm xs := by
  unfold exchange
  repeat' split
  all_goals first | exact Array.swap_perm _ _ | exact .refl _


theorem network_perm (gs : List Gate) (xs : Array Nat) :
    (gs.foldl (fun a g => exchange g a) xs).Perm xs := by
  induction gs generalizing xs with
  | nil => exact .refl _
  | cons g gs ih => exact (ih (exchange g xs)).trans (exchange_perm g xs)

theorem threshold_gate (t a b : Nat) :
    (decide (t ≤ min a b), decide (t ≤ max a b)) =
      (decide (t ≤ a) && decide (t ≤ b), decide (t ≤ a) || decide (t ≤ b)) := by
  by_cases h : a ≤ b
  · simp [min_eq_left h, max_eq_right h]; omega
  · have h' : b ≤ a := by omega
    simp [min_eq_right h', max_eq_left h']; omega

theorem ordered_of_threshold (a b : Nat)
    (h : ∀ t, t ≤ a → t ≤ b) : a ≤ b := h a (Nat.le_refl _)

end M31Comparator
