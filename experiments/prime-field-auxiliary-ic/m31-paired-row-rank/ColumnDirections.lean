import Mathlib.LinearAlgebra.Matrix.Rank

namespace PublicRowRank

variable {K Row Col Dir : Type*} [Field K] [Fintype Col] [Fintype Dir]

/-- Columns assigned to the same direction must be exact scalar multiples of its
representative. A zero column can be omitted or given scale zero. -/
theorem rank_le_column_directions (A : Matrix Row Col K) (basisCols : Matrix Row Dir K)
    (label : Col → Dir) (scale : Col → K)
    (entries : ∀ i j, A i j = basisCols i (label j) * scale j) :
    A.rank ≤ Fintype.card Dir := by
  classical
  let weights : Matrix Dir Col K := fun d j => if d = label j then scale j else 0
  have factorization : A = basisCols * weights := by
    ext i j
    simp [Matrix.mul_apply, weights, mul_ite, entries]
  rw [factorization]
  exact (Matrix.rank_mul_le_left _ _).trans basisCols.rank_le_card_width

/-- Fewer certified directions than rows imply a row dependency. -/
theorem dependent_of_fewer_directions [Fintype Row] (A : Matrix Row Col K)
    (basisCols : Matrix Row Dir K) (label : Col → Dir) (scale : Col → K)
    (entries : ∀ i j, A i j = basisCols i (label j) * scale j)
    (few : Fintype.card Dir < Fintype.card Row) : ¬ LinearIndependent K A.row := by
  intro independent
  have deficit := lt_of_le_of_lt (rank_le_column_directions A basisCols label scale entries) few
  exact (ne_of_lt deficit) independent.rank_matrix

end PublicRowRank
