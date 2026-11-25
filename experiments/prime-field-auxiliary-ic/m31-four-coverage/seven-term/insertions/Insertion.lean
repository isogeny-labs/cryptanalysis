import Mathlib

namespace M31Insertion
open Finset
/-- Any dependence modulo the old span can be evaluated at the private
coordinate of each new row. -/
theorem private_coefficients {K I J : Type*} [Field K] [Fintype J] [DecidableEq J]
    (old : Submodule K (I → K)) (row : J → I → K) (pivot : J → I)
    (vanishes : ∀ v ∈ old, ∀ j, v (pivot j) = 0)
    (diag : ∀ j, row j (pivot j) ≠ 0)
    (off : ∀ i j, i ≠ j → row i (pivot j) = 0)
    (c : J → K) (dep : ∑ j, c j • row j ∈ old) (j : J) : c j = 0 := by
  have h := vanishes _ dep j
  simp only [Finset.sum_apply, Pi.smul_apply, smul_eq_mul] at h
  rw [Finset.sum_eq_single j] at h
  · exact (mul_eq_zero.mp h).resolve_right (diag j)
  · intro i _ hij
    simp [off i j hij]
  · simp

theorem extra_point {X : Type*} [DecidableEq X] (old translated expanded : Finset X)
    (base : old.card = 61056) (bound : translated.card ≤ 800)
    (gain : 61856 < expanded.card) : ∃ x ∈ expanded, x ∉ old ∪ translated := by
  by_contra! h
  have le := (card_le_card h).trans (card_union_le old translated)
  omega
end M31Insertion
