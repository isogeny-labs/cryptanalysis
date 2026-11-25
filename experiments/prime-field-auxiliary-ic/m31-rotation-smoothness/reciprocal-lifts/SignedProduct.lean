import Mathlib.NumberTheory.LegendreSymbol.Basic
import Mathlib.Tactic.Ring

namespace ReciprocalLifts

variable (p : ℕ) [Fact p.Prime]

/-- Encode a nonzero residue's quadratic character in the sign of its integer lift. -/
def signedProduct (x : ℤ) : ℤ := legendreSym p x * x

theorem signedProduct_mul (x q : ℤ) :
    signedProduct p (x * q) = signedProduct p x * signedProduct p q := by
  unfold signedProduct
  rw [legendreSym.mul]
  ring

theorem signedProduct_negative (x : ℤ) (hx : 0 < x) (hn : (x : ZMod p) ≠ 0) :
    signedProduct p x < 0 ↔ ¬ IsSquare (x : ZMod p) := by
  rw [← legendreSym.eq_neg_one_iff]
  rcases legendreSym.eq_one_or_neg_one p hn with h | h <;> simp [signedProduct, h, hx, hx.not_gt]

end ReciprocalLifts
