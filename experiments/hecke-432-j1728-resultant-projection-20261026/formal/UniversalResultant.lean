import Mathlib.LinearAlgebra.Matrix.Determinant.Basic
import Mathlib.Tactic.Ring

namespace J1728Projection

variable {R : Type*} [CommRing R]

def sylvester (a b c z : R) : Matrix (Fin 5) (Fin 5) R :=
  !![1, -z, 0, -64, 0;
     0, 1, -z, 0, -64;
     a, b, c, 0, 0;
     0, a, b, c, 0;
     0, 0, a, b, c]

def formula (a b c z : R) : R :=
  4096 * a ^ 3 - 128 * a ^ 2 * c * z + 64 * a * b ^ 2 * z
    - 192 * a * b * c + a * c ^ 2 * z ^ 2
    + 64 * b ^ 3 + b * c ^ 2 * z + c ^ 3

/-- The degree-three/degree-two Sylvester determinant has eight terms. -/
theorem sylvester_resultant_formula (a b c z : R) :
    (sylvester a b c z).det = formula a b c z := by
  classical
  simp [sylvester, formula, Matrix.det_succ_row_zero,
    Fin.sum_univ_succ, Fin.succAbove]
  ring

#print axioms sylvester_resultant_formula

end J1728Projection
