import Mathlib.Data.ZMod.Basic
import Mathlib.Algebra.BigOperators.Ring.Finset
import Mathlib.Tactic

namespace M31Parity

/-- Reduction of a verified integer dependence after dropping any rows
whose weights vanish in characteristic two. -/
theorem parity_balance {I J : Type*} [Fintype I] (rows : I → J → ℤ) (weights : I → ℤ)
    (keep : Finset I) (balance : ∀ j, ∑ i, weights i * rows i j = 0)
    (drop : ∀ i, i ∉ keep → (weights i : ZMod 2) = 0) (j : J) :
    ∑ i ∈ keep, (weights i : ZMod 2) * (rows i j : ZMod 2) = 0 := by
  calc
    _ = ∑ i, (weights i : ZMod 2) * (rows i j : ZMod 2) := by
      apply Finset.sum_subset (Finset.subset_univ keep)
      intro i _ hi
      rw [drop i hi, zero_mul]
    _ = 0 := by exact_mod_cast congrArg (fun z : ℤ => (z : ZMod 2)) (balance j)

#print axioms parity_balance
end M31Parity
