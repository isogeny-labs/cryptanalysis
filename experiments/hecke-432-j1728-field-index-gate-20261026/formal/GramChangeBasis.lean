import Mathlib.LinearAlgebra.Matrix.Determinant.Basic
import Mathlib.Tactic.Ring

namespace J1728FieldIndex

variable {R : Type*} [CommRing R]
variable {n : Type*} [Fintype n] [DecidableEq n]

/-- The Gram determinant changes by the square of a basis-change determinant. -/
theorem gram_change_basis (traceGram change : Matrix n n R) :
    (change.transpose * traceGram * change).det =
      change.det ^ 2 * traceGram.det := by
  rw [Matrix.det_mul, Matrix.det_mul, Matrix.det_transpose]
  ring

#print axioms gram_change_basis

end J1728FieldIndex
