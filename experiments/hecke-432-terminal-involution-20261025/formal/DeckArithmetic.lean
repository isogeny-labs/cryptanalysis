import Mathlib.Data.Matrix.Mul
import Mathlib.Algebra.BigOperators.Fin
import Mathlib.Tactic.NormNum
import Mathlib.Tactic.FinCases

namespace DeckArithmetic

private def gamma : Matrix (Fin 2) (Fin 2) ℤ := ![![1, 0], ![216, 1]]

/-- The explicit coset representative squares to an element of Γ₀(432). -/
theorem gamma_square : gamma * gamma = ![![1, 0], ![432, 1]] := by
  obtain ⟨h00, h01, h10, h11⟩ := Matrix.two_mul_expl gamma gamma
  funext i j
  fin_cases i <;> fin_cases j
  · simpa [gamma] using h00
  · simpa [gamma] using h01
  · simpa [gamma] using h10
  · simpa [gamma] using h11

/-- Its lower-left entry lies at level 216 and outside level 432. -/
theorem gamma_exact_lower_level :
    (216 : ℤ) ∣ gamma 1 0 ∧ ¬ (432 : ℤ) ∣ gamma 1 0 := by
  norm_num [gamma]

#print axioms gamma_square
#print axioms gamma_exact_lower_level

end DeckArithmetic
