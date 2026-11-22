import Mathlib.LinearAlgebra.Matrix.Rank

namespace SeparationRank
variable {F : Type*} [Field F] {n r : Nat}

/-- If a sampled bivariate function factors through r scalar terms, a
right-inverse witness on an n-by-n minor forces at least n terms. -/
theorem lower_bound (U : Matrix (Fin n) (Fin r) F)
    (V : Matrix (Fin r) (Fin n) F) (C : Matrix (Fin n) (Fin n) F)
    (h : (U * V) * C = 1) : n ≤ r := by
  calc
    n = (1 : Matrix (Fin n) (Fin n) F).rank := by simp
    _ = ((U * V) * C).rank := by rw [h]
    _ ≤ (U * V).rank := Matrix.rank_mul_le_left _ _
    _ ≤ U.rank := Matrix.rank_mul_le_left _ _
    _ ≤ r := Matrix.rank_le_width _

#print axioms lower_bound
end SeparationRank
