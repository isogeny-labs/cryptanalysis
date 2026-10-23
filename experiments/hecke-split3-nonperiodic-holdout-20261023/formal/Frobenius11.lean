module

public import Mathlib.Tactic.Linarith
public import Mathlib.Tactic.Ring
public import Mathlib.Algebra.Ring.Rat

/-! Exact mod-11 characteristic-polynomial obstruction for the D=-551 field. -/
namespace Frobenius11

public theorem characteristic_polynomial_has_no_root :
    ∀ x : Fin 11, (((x.val : ℤ) ^ 2 - 176 * x.val + 12703) % 11) ≠ 0 := by
  decide

public theorem determinant_identity (a b c d x : ℤ)
    (trace : a + d = 176) (det : a * d - b * c = 12703) :
    (a - x) * (d - x) - b * c = x ^ 2 - 176 * x + 12703 := by
  calc
    (a - x) * (d - x) - b * c = x ^ 2 - (a + d) * x + (a * d - b * c) := by ring
    _ = x ^ 2 - 176 * x + 12703 := by rw [trace, det]

end Frobenius11

#print axioms Frobenius11.characteristic_polynomial_has_no_root
#print axioms Frobenius11.determinant_identity
